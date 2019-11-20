var g_previousX;
var g_previousY;
var g_backgroundImageData;
var g_imageData;
var g_image;
var g_segmentation;
var g_backgroundImage;
var g_segmentationData;
var g_paint = false;
var g_frameNr;
var g_currentColor = null;

function colorDistance(labelColor, colorArray) {
    var red = labelColor.red - colorArray[0];
    var green = labelColor.green - colorArray[1];
    var blue = labelColor.blue - colorArray[2];

    return red*red + green*green + blue*blue;
}

function loadOldSegmentation(task_id, image_id) {
    var oldSegmentationImage = new Image();
    oldSegmentationImage.src = '/segmentation/show/' + task_id + '/' + image_id + '/';
    oldSegmentationImage.onload = function() {
        // Transfer pixels to segmentationData
        console.log("Old segmentation was found");
        // Create dummy canvas to get access to pixels
        var dummyCanvas = document.createElement('canvas');
        dummyCanvas.setAttribute('width', g_canvasWidth);
        dummyCanvas.setAttribute('height', g_canvasHeight);
        // IE stuff
        if(typeof G_vmlCanvasManager != 'undefined') {
            dummyCanvas = G_vmlCanvasManager.initElement(dummyCanvas);
        }

        // Put segmentation into canvas
        var ctx = dummyCanvas.getContext('2d');
        ctx.drawImage(this, 0, 0, g_canvasWidth, g_canvasHeight);
        var oldSegmentationData = ctx.getImageData(0, 0, g_canvasWidth, g_canvasHeight).data;

        // Remove any non-label pixels from segmentation data (may happen if some smoothing of png occurs in browser)
        for(var i = 0; i < g_canvasWidth*g_canvasHeight; i++) {
            var color = [oldSegmentationData[i*4], oldSegmentationData[i*4+1], oldSegmentationData[i*4+2]];
            var useColor = {
                red: 0,
                green: 0,
                blue: 0
            };
            if(colorDistance(useColor, color) > 20) {
                // For each label, find closest color
                var currentMinDistance = 1000000;
                for (var l = 0; l < g_labelButtons.length; l++) {
                    var labelButton = g_labelButtons[l];
                    if (colorDistance(labelButton, color) < currentMinDistance) {
                        currentMinDistance = colorDistance(labelButton, color);
                        useColor.red = labelButton.red;
                        useColor.green = labelButton.green;
                        useColor.blue = labelButton.blue;
                    }
                }
            }

            oldSegmentationData[i*4] = useColor.red;
            oldSegmentationData[i*4+1] = useColor.green;
            oldSegmentationData[i*4+2] = useColor.blue;
        }

        // Put pixels into imageData and segmentationData
        for(var i = 0; i < g_canvasWidth*g_canvasHeight; i++) {
            if(oldSegmentationData[i*4] > 0 || oldSegmentationData[i*4+1] > 0 || oldSegmentationData[i*4+2] > 0) {
                g_imageData[i*4] = oldSegmentationData[i*4];
                g_imageData[i*4+1] = oldSegmentationData[i*4+1];
                g_imageData[i*4+2] = oldSegmentationData[i*4+2];
                g_segmentationData[i*4] = oldSegmentationData[i*4];
                g_segmentationData[i*4+1] = oldSegmentationData[i*4+1];
                g_segmentationData[i*4+2] = oldSegmentationData[i*4+2];
            }
        }

        redraw();
    };
}

function setupSegmentation() {
    // Initialize canvas with background image
    g_context.clearRect(0, 0, g_context.canvas.width, g_context.canvas.height); // Clears the canvas
    g_context.drawImage(g_backgroundImage, 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
    g_backgroundImageData = g_context.getImageData(0,0,g_canvasWidth, g_canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    g_image = g_context.getImageData(0, 0, g_canvasWidth, g_canvasHeight);
    g_imageData = g_image.data;

    // Create segmentation image
    g_segmentation = g_context.createImageData(g_canvasWidth, g_canvasHeight);
    g_segmentationData = g_segmentation.data;
    for(var i = 0; i < g_canvasWidth*g_canvasHeight; i++) {
        g_segmentationData[i*4+3] = 255;
    }
    loadOldSegmentation(g_taskID, g_imageID);


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

        g_paint = true;
        g_previousX = mouseX;
        g_previousY = mouseY;
        addClick(mouseX, mouseY, false);
        redraw();
    });

    $('#canvas').mousemove(function(e) {
        if(g_paint) {
            var scale =  g_canvasWidth / $('#canvas').width();
            var mouseX = (e.pageX - this.offsetLeft)*scale;
            var mouseY = (e.pageY - this.offsetTop)*scale;
            addClick(mouseX, mouseY, true);
            redraw();
        }
    });

    $('#canvas').mouseup(function(e){
        g_paint = false;
        //segmentationHistory.push(currentAction); // Add action to history
    });

    $('#canvas').mouseleave(function(e){
        if(g_paint) {

            var scale =  g_canvasWidth / $('#canvas').width();
            var mouseX = (e.pageX - this.offsetLeft)*scale;
            var mouseY = (e.pageY - this.offsetTop)*scale;
            if(mouseX >= g_canvasWidth)
                mouseX = g_canvasWidth-1;
            if(mouseY >= g_canvasHeight)
                mouseY = g_canvasHeight-1;
            if(mouseX < 0)
                mouseX = 0;
            if(mouseY < 0)
                mouseY = 0;
            addClick(mouseX, mouseY, true);
            redraw();
            g_paint = false;
            //segmentationHistory.push(currentAction); // Add action to history
        }
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        for(var i = 0; i < g_canvasWidth*g_canvasHeight; i++) {
            g_segmentationData[i*4] = 0;
            g_segmentationData[i*4+1] = 0;
            g_segmentationData[i*4+2] = 0;
            g_segmentationData[i*4+3] = 255;
            g_imageData[i*4] = g_backgroundImageData[i*4];
            g_imageData[i*4+1] = g_backgroundImageData[i*4+1];
            g_imageData[i*4+2] = g_backgroundImageData[i*4+2];
            g_imageData[i*4+3] = 255;
        }

        $('#slider').slider('value', g_frameNr); // Update slider
        redraw();
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id)
}

function sendDataForSave() {
    // Create a new canvas to put segmentation in
    var dummyCanvas = document.createElement('canvas');
    dummyCanvas.setAttribute('width', g_canvasWidth);
    dummyCanvas.setAttribute('height', g_canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        dummyCanvas = G_vmlCanvasManager.initElement(dummyCanvas);
    }

    // Put segmentation into canvas
    var ctx = dummyCanvas.getContext('2d');
    ctx.putImageData(g_segmentation, 0, 0);
    var dataURL = dummyCanvas.toDataURL('image/png', 1); // Use png to compress image and save bandwidth

    return $.ajax({
        type: "POST",
        url: "/segmentation/save/",
        data: {
            image: dataURL,
            width: g_canvasWidth,
            height: g_canvasHeight,
            image_id: g_imageID,
            task_id: g_taskID,
            quality: $('input[name=quality]:checked').val(),
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadSegmentation(image_sequence_id, frame_nr, task_id, image_id) {
    console.log('In segmentation load')

    g_backgroundImage = new Image();
    g_frameNr = frame_nr;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/' + g_taskID + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupSegmentation(task_id, image_id);
    };

}

function addClick(x, y, dragging) {
    g_annotationHasChanged = true;
    //var label = labels[activeLabel];
    var color = g_currentColor;
    var brushRadius = 1;
    //if(label.name == "Eraser") {
    //    brushRadius = 3;
    //}
    // Draw a line from previousX, previousY to x, y
    if(dragging) {
        var directionX = x - g_previousX;
        var directionY = y - g_previousY;
        var length = Math.sqrt(directionX*directionX+directionY*directionY);
        directionX /= length;
        directionY /= length;
        for(var i = 0; i < length; i++) {
            var currentX = g_previousX + directionX*i;
            var currentY = g_previousY + directionY*i;
            currentX = Math.round(currentX);
            currentY = Math.round(currentY);
            drawAtPoint(currentX, currentY, g_canvasWidth, brushRadius, color);
        }
        g_previousX = x;
        g_previousY = y;
    } else {
        drawAtPoint(x, y, g_canvasWidth, brushRadius, color);
    }
}

function drawAtPoint(x, y, width, brushRadius, color) {
    for(var a = -brushRadius; a <= brushRadius; a++) {
        for(var b = -brushRadius; b <= brushRadius; b++) {
            var currentX = x + a;
            var currentY = y + b;
            // Check for out of bounds
            if(currentX >= g_canvasWidth)
                currentX = g_canvasWidth-1;
            if(currentY >= g_canvasHeight)
                currentY = g_canvasHeight-1;
            if(currentX < 0)
                currentX = 0;
            if(currentY < 0)
                currentY = 0;
            g_segmentationData[(currentX + currentY*g_canvasWidth)*4] = color.red;
            g_segmentationData[(currentX + currentY*g_canvasWidth)*4+1] = color.green;
            g_segmentationData[(currentX + currentY*g_canvasWidth)*4+2] = color.blue;
            g_imageData[(currentX + currentY*g_canvasWidth)*4] = color.red;
            g_imageData[(currentX + currentY*g_canvasWidth)*4+1] = color.green;
            g_imageData[(currentX + currentY*g_canvasWidth)*4+2] = color.blue;
            var position = {x: currentX, y: currentY};
        }
    }
}

function redraw(){
    g_context.putImageData(g_image, 0, 0);
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
