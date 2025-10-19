/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const fieldRegistry = registry.category("fields");

class ScreenPatternWidget extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.canvas = undefined;
        this.ctx = undefined;
        this.isDrawing = false;
        this.onPointerDown = this.onPointerDown.bind(this);
        this.onPointerMove = this.onPointerMove.bind(this);
        this.onPointerUp = this.onPointerUp.bind(this);
        this.onPointerLeave = this.onPointerLeave.bind(this);
        onMounted(() => this.initializeCanvas());
        onWillUnmount(() => this.teardown());
    }

    initializeCanvas(value = this.props.value) {
        if (this.props.readonly) {
            return;
        }
        const canvas = this.canvasRef.el;
        if (!canvas) {
            return;
        }
        if (this.canvas !== canvas) {
            this.teardown();
            this.canvas = canvas;
            this.ctx = canvas.getContext("2d");
            const size = 320;
            this.canvas.width = size;
            this.canvas.height = size;
            this.canvas.style.touchAction = "none";
            this.canvas.addEventListener("pointerdown", this.onPointerDown);
            this.canvas.addEventListener("pointermove", this.onPointerMove);
            this.canvas.addEventListener("pointerup", this.onPointerUp);
            this.canvas.addEventListener("pointercancel", this.onPointerUp);
            this.canvas.addEventListener("pointerleave", this.onPointerLeave);
        }
        this.drawWatermark();
        if (value) {
            this.drawExistingImage(value);
        }
    }

    teardown() {
        if (!this.canvas) {
            return;
        }
        this.canvas.removeEventListener("pointerdown", this.onPointerDown);
        this.canvas.removeEventListener("pointermove", this.onPointerMove);
        this.canvas.removeEventListener("pointerup", this.onPointerUp);
        this.canvas.removeEventListener("pointercancel", this.onPointerUp);
        this.canvas.removeEventListener("pointerleave", this.onPointerLeave);
        this.canvas = undefined;
        this.ctx = undefined;
    }

    drawWatermark() {
        if (!this.ctx) {
            return;
        }
        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);
        this.ctx.fillStyle = "#f8fafc";
        this.ctx.fillRect(0, 0, width, height);
        const padding = width * 0.18;
        const rows = 3;
        const cols = 3;
        const spacingX = (width - padding * 2) / (cols - 1);
        const spacingY = (height - padding * 2) / (rows - 1);
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const x = padding + col * spacingX;
                const y = padding + row * spacingY;
                this.ctx.beginPath();
                this.ctx.arc(x, y, 10, 0, Math.PI * 2, false);
                this.ctx.fillStyle = "#d1d5db";
                this.ctx.fill();
                this.ctx.beginPath();
                this.ctx.arc(x, y, 4, 0, Math.PI * 2, false);
                this.ctx.fillStyle = "#9ca3af";
                this.ctx.fill();
            }
        }
    }

    drawExistingImage(value) {
        if (!value || !this.ctx) {
            return;
        }
        const image = new Image();
        image.onload = () => {
            this.ctx.drawImage(image, 0, 0, this.canvas.width, this.canvas.height);
        };
        image.src = `data:image/png;base64,${value}`;
    }

    onPointerDown(ev) {
        if (this.props.readonly || !this.ctx) {
            return;
        }
        ev.preventDefault();
        const { x, y } = this.getRelativePosition(ev);
        this.isDrawing = true;
        this.ctx.strokeStyle = "#2563eb";
        this.ctx.lineWidth = 6;
        this.ctx.lineCap = "round";
        this.ctx.lineJoin = "round";
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
    }

    onPointerMove(ev) {
        if (!this.isDrawing || !this.ctx) {
            return;
        }
        ev.preventDefault();
        const { x, y } = this.getRelativePosition(ev);
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
    }

    onPointerUp(ev) {
        if (!this.isDrawing || !this.ctx) {
            return;
        }
        ev.preventDefault();
        this.isDrawing = false;
        this.ctx.closePath();
        this.saveValue();
    }

    onPointerLeave(ev) {
        if (!this.isDrawing) {
            return;
        }
        this.onPointerUp(ev);
    }

    getRelativePosition(ev) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: ev.clientX - rect.left,
            y: ev.clientY - rect.top,
        };
    }

    saveValue() {
        if (!this.canvas) {
            return;
        }
        const dataUrl = this.canvas.toDataURL("image/png");
        const base64 = dataUrl.split(",")[1];
        this.props.update(base64);
    }

    onClear() {
        if (!this.ctx) {
            return;
        }
        this.drawWatermark();
        this.props.update(false);
    }

    willUpdateProps(nextProps) {
        if (nextProps.readonly && !this.props.readonly) {
            this.teardown();
        }
        if (!nextProps.readonly) {
            Promise.resolve().then(() => this.initializeCanvas(nextProps.value));
        }
    }
}

ScreenPatternWidget.template = "mobile_service_shop.ScreenPatternWidget";
ScreenPatternWidget.props = standardFieldProps;

fieldRegistry.add("screen_pattern_drawer", ScreenPatternWidget);

export default ScreenPatternWidget;
