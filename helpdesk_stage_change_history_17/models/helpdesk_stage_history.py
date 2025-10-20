from odoo import api, fields, models

class HelpdeskStageHistory(models.Model):
    _name = "helpdesk.stage.history"
    _description = "Helpdesk Ticket Stage Change History"
    _order = "start_datetime desc, id desc"

    ticket_id = fields.Many2one("helpdesk.ticket", required=True, ondelete="cascade", index=True, string="Ticket")
    stage_id = fields.Many2one("helpdesk.stage", required=True, index=True, string="Stage")
    start_datetime = fields.Datetime(string="Entered At", required=True, default=fields.Datetime.now, index=True)
    end_datetime = fields.Datetime(string="Left At", index=True)
    duration_hours = fields.Float(string="Duration (hours)", compute="_compute_duration", store=True)
    duration_display = fields.Char(string="Duration", compute="_compute_duration_display")
    changed_by = fields.Many2one("res.users", string="Changed By", default=lambda self: self.env.user, index=True)
    is_open = fields.Boolean(string="Open Interval", compute="_compute_is_open", store=True)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_is_open(self):
        for rec in self:
            rec.is_open = not bool(rec.end_datetime)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = fields.Datetime.from_string(rec.end_datetime) - fields.Datetime.from_string(rec.start_datetime)
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration_display(self):
        for rec in self:
            if rec.start_datetime:
                end = rec.end_datetime or fields.Datetime.now()
                delta = fields.Datetime.from_string(end) - fields.Datetime.from_string(rec.start_datetime)
                seconds = int(delta.total_seconds())
                h = seconds // 3600
                m = (seconds % 3600) // 60
                s = seconds % 60
                rec.duration_display = f"{h}h {m}m {s}s"
            else:
                rec.duration_display = "0h 0m 0s"

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    stage_history_ids = fields.One2many("helpdesk.stage.history", "ticket_id", string="Stage History", readonly=True)
    last_stage_change = fields.Datetime(string="Last Stage Change", readonly=True)

    def _create_initial_stage_history(self):
        for ticket in self:
            if ticket.stage_id:
                self.env['helpdesk.stage.history'].sudo().create({
                    'ticket_id': ticket.id,
                    'stage_id': ticket.stage_id.id,
                    'start_datetime': fields.Datetime.now(),
                    'changed_by': self.env.user.id,
                })
                ticket.sudo().write({'last_stage_change': fields.Datetime.now()})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.sudo()._create_initial_stage_history()
        return records

    def write(self, vals):
        track_stage = 'stage_id' in vals
        old_stages = {}
        if track_stage:
            for t in self:
                old_stages[t.id] = t.stage_id.id
        res = super().write(vals)
        if track_stage:
            now = fields.Datetime.now()
            for t in self:
                prev_stage_id = old_stages.get(t.id)
                new_stage_id = t.stage_id.id
                if prev_stage_id and new_stage_id and prev_stage_id != new_stage_id:
                    last_line = self.env['helpdesk.stage.history'].sudo().search([
                        ('ticket_id', '=', t.id),
                    ], limit=1, order="start_datetime desc, id desc")
                    if last_line and not last_line.end_datetime:
                        last_line.sudo().write({'end_datetime': now})
                    self.env['helpdesk.stage.history'].sudo().create({
                        'ticket_id': t.id,
                        'stage_id': new_stage_id,
                        'start_datetime': now,
                        'changed_by': self.env.user.id,
                    })
                    t.sudo().write({'last_stage_change': now})
        return res

    def action_backfill_stage_history(self):
        History = self.env['helpdesk.stage.history'].sudo()
        for t in self:
            if not t.stage_history_ids and t.stage_id:
                History.create({
                    'ticket_id': t.id,
                    'stage_id': t.stage_id.id,
                    'start_datetime': t.create_date or fields.Datetime.now(),
                    'changed_by': self.env.user.id,
                })
        return True