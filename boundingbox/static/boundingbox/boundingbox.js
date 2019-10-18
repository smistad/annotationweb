var g_backgroundImage;
var g_paint = false;
var g_frameNr;
var g_currentColor = null;
var g_BBx;
var g_BBy;
var g_BBx2;
var g_BBy2;
var g_boxes = {}; // Dictionary with keys frame_nr which each has a list of boxes
var g_minimumSize = 10;

function setupSegmentation() {
    console.log('setting up segmentation....');

    // Define event callbacks
    $('#canvas').mousedown(function(e) {

        // TODO check if current frame is not the frame to segment

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;

        g_BBx = mouseX;
        g_BBy = mouseY;
        g_paint = true;
        console.log('started BB on ' + g_BBx + ' ' + g_BBy);
    });

    $('#canvas').mousemove(function(e) {
        if(g_paint) {
            var scale =  g_canvasWidth / $('#canvas').width();
            var mouseX = (e.pageX - this.offsetLeft)*scale;
            var mouseY = (e.pageY - this.offsetTop)*scale;
            g_BBx2 = mouseX;
            g_BBy2 = mouseY;
            redrawSequence();
        }
    });

    $('#canvas').mouseup(function(e){
        g_paint = false;
        g_annotationHasChanged = true;
        addBox(g_currentFrameNr, g_BBx, g_BBy, g_BBx2, g_BBy2, g_currentLabel);
        console.log('finished BB on ' + g_BBx + ' ' + g_BBy);
    });

    $('#canvas').mouseleave(function(e){
        if(g_paint) {
            g_annotationHasChanged = true;
            addBox(g_currentFrameNr, g_BBx, g_BBy, g_BBx2, g_BBy2, g_currentLabel);
            redrawSequence();
            g_paint = false;
        }
    });

    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_boxes = {};
        $('#slider').slider('value', g_frameNr); // Update slider
        redrawSequence();
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id);
    redrawSequence();
}

function createBox(x, y, x2, y2, label) {
    // Select the one closest to 0,0
    var boxOriginX = min(x, x2);
    var boxOriginY = min(y, y2);

    // Calculate width and height
    var width = max(x, x2) - boxOriginX;
    var height = max(y, y2) - boxOriginY;

    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id === label) {
            labelIndex = i;
        }
    }

    var box = {
        x: boxOriginX,
        y: boxOriginY,
        width: width,
        height: height,
        label_id: label, // actual DB id
        label: labelIndex // index: only used for color
    };
    return box;
}

function addBox(frame_nr, x, y, x2, y2, label) {
    // Only add box if large enough
    if(Math.abs(x2 - x) > g_minimumSize && Math.abs(y2 - y) > g_minimumSize) {
        var box = createBox(x, y, x2, y2, label);
        if(!(frame_nr in g_boxes))
            g_boxes[frame_nr] = [];
        g_boxes[frame_nr].push(box);
    }
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/boundingbox/save/",
        data: {
            image_id: g_imageID,
            boxes: JSON.stringify(g_boxes),
            task_id: g_taskID,
            target_frames: JSON.stringify(g_targetFrames),
            quality: $('input[name=quality]:checked').val(),
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadBBTask(image_sequence_id) {
    console.log('In bb task load')

    g_backgroundImage = new Image();
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + 0 + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupSegmentation();
    };

}

function redraw(){
    var box, label;

    // Draw current box
    if(g_paint) {
        g_context.beginPath();
        g_context.lineWidth = 2;
        box = createBox(g_BBx, g_BBy, g_BBx2, g_BBy2, g_currentLabel);
        label = g_labelButtons[box.label];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        g_context.rect(box.x, box.y, box.width, box.height);
        g_context.stroke();
    }

    if(!(g_currentFrameNr in g_boxes))
        return;

    // Draw all stores boxes
    for(var i = 0; i < g_boxes[g_currentFrameNr].length; ++i) {
        g_context.beginPath();
        g_context.lineWidth = 2;
        box = g_boxes[g_currentFrameNr][i];
        label = g_labelButtons[box.label];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        g_context.rect(box.x, box.y, box.width, box.height);
        g_context.stroke();
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();
}
