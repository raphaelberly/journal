var slider = document.getElementById("gradeRange");
var output = document.getElementById("gradeValue");
output.innerHTML = slider.value;

slider.oninput = function() {
    <!-- Set the toFixed value to 1 to have a fixed 1-decimal printed value -->
    output.innerHTML = parseFloat(this.value).toFixed(gradePrecision);
}
