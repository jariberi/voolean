/**
 * Created by jorge on 19/11/2015.
 */

function toggleBlock() {
    //blockh4=objeto jquery
    //div > h4 + a*i
    var a = $(this);
    a.parent().find('a').each(function () {
        if ($(this).is(':visible')) {
            $(this).hide(300);
        } else {
            $(this).show("slow").css("display", "block");
        }
    });
}

function redondear(numero, decimales) {
    var flotante = parseFloat(numero);
    var resultado = Math.round(flotante * Math.pow(10, decimales)) / Math.pow(10, decimales);
    return resultado.toFixed(decimales);
}

function convertDate(inputFormat) {
    function pad(s) {
        return (s < 10) ? '0' + s : s;
    }

    var d = new Date(inputFormat);
    return [pad(d.getDate()), pad(d.getMonth() + 1), d.getFullYear()].join('/');
}