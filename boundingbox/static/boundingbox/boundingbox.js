var backgroundImageData;
var imageData;
var image;
var backgroundImage;
var paint = false;
var frameNr;
var currentColor = null;
var labelButtons = [];
var currentLabel = 0;
var BBx;
var BBy;
var BBx2;
var BBy2;
var boxes = [];

function setupSegmentation(task_id, image_id) {
    g_taskID = task_id;
    g_imageID = image_id;

    // Initialize canvas with background image
    context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas
    context.drawImage(backgroundImage, 0, 0, canvasWidth, canvasHeight); // Draw background image
    backgroundImageData = context.getImageData(0,0,canvasWidth, canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    image = context.getImageData(0, 0, canvasWidth, canvasHeight);
    imageData = image.data;

    // Define event callbacks
    $('#canvas').mousedown(function(e) {

        // If current frame is not the frame to segment
        if(currentFrameNr != frameNr) {
            // Move slider to frame to segment
            $('#slider').slider("value", frameNr);
            currentFrameNr = frameNr;
            redraw();
            return;
        }

        var mouseX = e.pageX - this.offsetLeft;
        var mouseY = e.pageY - this.offsetTop;

        BBx = mouseX;
        BBy = mouseY;
        paint = true;
        console.log('started BB on ' + BBx + ' ' + BBy);
    });

    $('#canvas').mousemove(function(e) {
        if(paint) {
            var mouseX = e.pageX - this.offsetLeft;
            var mouseY = e.pageY - this.offsetTop;
            BBx2 = mouseX;
            BBy2 = mouseY;
            redraw();
        }
    });

    $('#canvas').mouseup(function(e){
        paint = false;
        addBox(BBx, BBy, BBx2, BBy2, currentLabel);
        console.log('finished BB on ' + BBx + ' ' + BBy);
        //segmentationHistory.push(currentAction); // Add action to history
    });

    $('#canvas').mouseleave(function(e){
        if(paint) {
            addBox(BBx, BBy, BBx2, BBy2, currentLabel);
            redraw();
            paint = false;
            //segmentationHistory.push(currentAction); // Add action to history
        }
    });


    $("#clearButton").click(function() {
        boxes = [];
        $('#slider').slider('value', frameNr); // Update slider
        redraw();
    });

    // Set first label active
    changeLabel(labelButtons[0].id);
    redraw();
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
    for(var i = 0; i < labelButtons.length; i++) {
        if(labelButtons[i].id == label) {
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

function addBox(x, y, x2, y2, label) {

    var box = createBox(x, y, x2, y2, label);
    boxes.push(box);
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/boundingbox/save/",
        data: {
            image_id: g_imageID,
            boxes: JSON.stringify(boxes),
            task_id: g_taskID,
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadBBTask(image_sequence_id, frame_nr, task_id, image_id) {
    console.log('In bb task load')

    backgroundImage = new Image();
    frameNr = frame_nr;
    backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    backgroundImage.onload = function() {
        canvasWidth = this.width;
        canvasHeight = this.height;
        setupSegmentation(task_id, image_id);
    };

}

function redraw(){
    context.putImageData(image, 0, 0);
    // Draw all stores boxes
    for(var i = 0; i < boxes.length; ++i) {
        context.beginPath();
        context.lineWidth = 2;
        var box = boxes[i];
        var label = labelButtons[box.label];
        context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        context.rect(box.x, box.y, box.width, box.height);
        context.stroke();
    }
    // Draw current box
    if(paint) {
        context.beginPath();
        context.lineWidth = 2;
        var box = createBox(BBx, BBy, BBx2, BBy2, currentLabel);
        var label = labelButtons[box.label];
        context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        context.rect(box.x, box.y, box.width, box.height);
        context.stroke();
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    if(currentFrameNr == frameNr) {
        redraw();
    } else {
        var index = currentFrameNr - startFrame;
        context.drawImage(sequence[index], 0, 0, canvasWidth, canvasHeight);
    }
}
