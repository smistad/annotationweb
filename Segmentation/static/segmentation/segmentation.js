var previousX;
var previousY;
var backgroundImageData;
var imageData;
var image;
var backgroundImage;
var segmentationData;
var paint = false;
var frameNr;
var currentColor = null;

function setupSegmentation() {
    // Initialize canvas with background image
    context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas
    context.drawImage(backgroundImage, 0, 0, canvasWidth, canvasHeight); // Draw background image
    backgroundImageData = context.getImageData(0,0,canvasWidth, canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    image = context.getImageData(0, 0, canvasWidth, canvasHeight);
    imageData = image.data;

    // Create segmentation image
    segmentation = context.createImageData(canvasWidth, canvasHeight);
    segmentationData = segmentation.data;
    for(var i = 0; i < canvasWidth*canvasHeight; i++) {
        segmentationData[i*4+3] = 255;
    }

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

        paint = true;
        previousX = mouseX;
        previousY = mouseY;
        currentAction = new Array();
        addClick(mouseX, mouseY, false);
        redraw();
    });

    $('#canvas').mousemove(function(e) {
        if(paint) {
            var mouseX = e.pageX - this.offsetLeft;
            var mouseY = e.pageY - this.offsetTop;
            addClick(mouseX, mouseY, true);
            redraw();
        }
    });

    $('#canvas').mouseup(function(e){
        paint = false;
        //segmentationHistory.push(currentAction); // Add action to history
    });

    $('#canvas').mouseleave(function(e){
        if(paint) {
            var mouseX = e.pageX - this.offsetLeft;
            var mouseY = e.pageY - this.offsetTop;
            if(mouseX >= canvasWidth)
                mouseX = canvasWidth-1;
            if(mouseY >= canvasHeight)
                mouseY = canvasHeight-1;
            if(mouseX < 0)
                mouseX = 0;
            if(mouseY < 0)
                mouseY = 0;
            addClick(mouseX, mouseY, true);
            redraw();
            paint = false;
            //segmentationHistory.push(currentAction); // Add action to history
        }
    });


    $("#clearButton").click(function() {
        for(var i = 0; i < canvasWidth*canvasHeight; i++) {
            segmentationData[i*4] = 0;
            segmentationData[i*4+1] = 0;
            segmentationData[i*4+2] = 0;
            segmentationData[i*4+3] = 255;
            imageData[i*4] = backgroundImageData[i*4];
            imageData[i*4+1] = backgroundImageData[i*4+1];
            imageData[i*4+2] = backgroundImageData[i*4+2];
            imageData[i*4+3] = 255;
        }

        redraw();
    });
}

function loadSegmentation(image_sequence_id, frame_nr) {
    console.log('In segmentation load')

    backgroundImage = new Image();
    frameNr = frame_nr;
    backgroundImage.src = '/annotation/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    backgroundImage.onload = function() {
        setupSegmentation();
    };

}

function addClick(x, y, dragging) {

    segmentationChanged = true;
    //var label = labels[activeLabel];
    var color = currentColor;
    if(color == null) {
        alert('Select label first.');
        return;
    }
    var brushRadius = 1;
    //if(label.name == "Eraser") {
    //    brushRadius = 3;
    //}
    // Draw a line from previousX, previousY to x, y
    if(dragging) {
        directionX = x - previousX;
        directionY = y - previousY;
        length = Math.sqrt(directionX*directionX+directionY*directionY);
        directionX /= length;
        directionY /= length;
        for(var i = 0; i < length; i++) {
            currentX = previousX + directionX*i;
            currentY = previousY + directionY*i;
            currentX = Math.round(currentX);
            currentY = Math.round(currentY);
            drawAtPoint(currentX, currentY, canvasWidth, brushRadius, color);
        }
        previousX = x;
        previousY = y;
    } else {
        drawAtPoint(x, y, canvasWidth, brushRadius, color);
    }
}

function drawAtPoint(x, y, width, brushRadius, color) {
    for(var a = -brushRadius; a <= brushRadius; a++) {
        for(var b = -brushRadius; b <= brushRadius; b++) {
            var currentX = x + a;
            var currentY = y + b;
            // Check for out of bounds
            if(currentX >= canvasWidth)
                currentX = canvasWidth-1;
            if(currentY >= canvasHeight)
                currentY = canvasHeight-1;
            if(currentX < 0)
                currentX = 0;
            if(currentY < 0)
                currentY = 0;
            // Check if eraser is used
            if(color.red == 0 && color.green == 0 && color.blue == 0) {
                // Remove segmentation and put background back
                segmentationData[(currentX + currentY*canvasWidth)*4] = 0;
                segmentationData[(currentX + currentY*canvasWidth)*4+1] = 0;
                segmentationData[(currentX + currentY*canvasWidth)*4+2] = 0;
                imageData[(currentX + currentY*canvasWidth)*4] = backgroundImageData[(currentX + currentY*canvasWidth)*4];
                imageData[(currentX + currentY*canvasWidth)*4+1] = backgroundImageData[(currentX + currentY*canvasWidth)*4+1];
                imageData[(currentX + currentY*canvasWidth)*4+2] = backgroundImageData[(currentX + currentY*canvasWidth)*4+2];
            } else {
                segmentationData[(currentX + currentY*canvasWidth)*4] = color.red;
                segmentationData[(currentX + currentY*canvasWidth)*4+1] = color.green;
                segmentationData[(currentX + currentY*canvasWidth)*4+2] = color.blue;
                imageData[(currentX + currentY*canvasWidth)*4] = color.red;
                imageData[(currentX + currentY*canvasWidth)*4+1] = color.green;
                imageData[(currentX + currentY*canvasWidth)*4+2] = color.blue;
                var position = {x: currentX, y: currentY};
                //currentAction.push(position);
            }
        }
    }
}

function redraw(){
    context.putImageData(image, 0, 0);
}

function changeColor(label_id, red, green, blue) {
    currentColor = {
        red: red,
        green: green,
        blue: blue
    };
}
