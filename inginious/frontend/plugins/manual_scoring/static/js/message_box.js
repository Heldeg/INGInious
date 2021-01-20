class MessageBox {
    constructor(divId, textContent, type, dismissible = true) {
        this.divElement = document.getElementById(divId);
        this.textContent = textContent;
        this.type = type;
        this.dismissible = dismissible;
        this.generateHtmlCode();
        this.displayBoxMessage();
    }

    displayBoxMessage() {
        this.divElement.innerHTML += this.code;
        this.divElement.style.display = "block";
        if (this.dismissible) {
            this.doDisappearEffect();
        }
    }

    doDisappearEffect() {
        let opacity = 1;
        const element = this.divElement;
        const timer = setInterval(function () {
            if (opacity <= 0.1) {
                element.style.display = "none";
                clearInterval(timer);
                element.innerHTML = "";
            }
            element.style.opacity = opacity;
            element.style.filter = "alpha(opacity=" + opacity * 100 + ")";
            opacity -= opacity * 0.05;
        }, 100);
    }

    generateHtmlCode() {
        let code = '<div class="alert fade in ';
        if (this.dismissible)
            code += 'alert-dismissible ';
        code += 'alert-' + this.type + '" role="alert">';
        if (this.dismissible)
            code += '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>';
        code += this.textContent;
        code += '</div>';
        this.code = code;
    }

}