var g_backgroundImageData;
var g_imageData;
var g_image;
var g_backgroundImage;
var g_frameNr;
var g_currentColor = null;
var g_landmarks = [];

function setupSegmentation() {

    // Initialize canvas with background image
    g_context.clearRect(0, 0, g_context.canvas.width, g_context.canvas.height); // Clears the canvas
    g_context.drawImage(g_backgroundImage, 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
    g_backgroundImageData = g_context.getImageData(0,0,g_canvasWidth, g_canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    g_image = g_context.getImageData(0, 0, g_canvasWidth, g_canvasHeight);
    g_imageData = g_image.data;

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        // If current frame is not the frame to segment
        if(g_currentFrameNr != g_frameNr) {
            // Move slider to frame to segment
            $('#slider').slider("value", g_frameNr);
            g_currentFrameNr = g_frameNr;
            redraw();
            return;
        }

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;

        addLandmark(mouseX, mouseY, g_currentLabel);
        redraw();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_landmarks = [];
        $('#slider').slider('value', g_frameNr); // Update slider
        redraw();
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id);
    redraw();
}

function createLandmark(x, y, label) {
    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == label) {
            labelIndex = i;
            break;
        }
    }

    var landmark = {
        x: x,
        y: y,
        label_id: label, // actual DB id
        label: labelIndex // index: only used for color
    };
    return landmark;
}

function addLandmark(x, y, label) {
    var landmark = createLandmark(x, y, label);
    g_landmarks.push(landmark);
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/landmark/save/",
        data: {
            image_id: g_imageID,
            landmarks: JSON.stringify(g_landmarks),
            task_id: g_taskID,
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadLandmarkTask(image_sequence_id, frame_nr) {
    console.log('In landmark task load')

    g_backgroundImage = new Image();
    g_frameNr = frame_nr;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupSegmentation();
    };

}

function redraw(){
    g_context.putImageData(g_image, 0, 0);
    var landmarkSize = 20;
    // Draw all stores landmarks
    for(var i = 0; i < g_landmarks.length; ++i) {
        g_context.beginPath();
        g_context.lineWidth = 3;
        var landmark = g_landmarks[i];
        var label = g_labelButtons[landmark.label];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        var y = landmark.y;
        var x = landmark.x;
        var start_x = landmark.x - landmarkSize/2;
        var start_y = landmark.y - landmarkSize/2;
        var end_x = landmark.x + landmarkSize/2;
        var end_y = landmark.y + landmarkSize/2;
        // Horizontal line
        g_context.moveTo(start_x, y);
        g_context.lineTo(end_x, y);
        // Vertical line
        g_context.moveTo(x, start_y);
        g_context.lineTo(x, end_y);
        g_context.stroke();
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    if(g_currentFrameNr == g_frameNr) {
        redraw();
    } else {
        var index = g_currentFrameNr - g_startFrame;
        g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    }
}
