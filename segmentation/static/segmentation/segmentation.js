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
var labelButtons = new Array();
var currentLabel = 0;

function setupSegmentation(task_id, image_id) {
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

        $('#slider').slider('value', frameNr); // Update slider
        redraw();
    });

    // This is required due to djangos CSRF protection
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $('#saveButton').mousedown(function(e) {
        var messageBox = document.getElementById("message")
        messageBox.innerHTML = '<span class="info">Please wait while saving image..</span>';
        sendDataForSave(task_id, image_id).done(function(data) {
            console.log("Save done..");
            console.log(data);
            var messageBox = document.getElementById("message")
            if(data.success == "true") {
                messageBox.innerHTML = '<span class="success">Image was saved</span>';
                // Refresh page
                location.reload();
            } else {
                messageBox.innerHTML = '<span class="error">Save failed! ' + data.message + '</span>';
            }
            console.log(data.message);
        }).fail(function(data) {
            console.log("Ajax failed");
            var messageBox = document.getElementById("message")
            messageBox.innerHTML = '<span class="error">Save failed!</span>';
        }).always(function(data) {
            console.log("Ajax complete");
        });
        console.log("Save button pressed");
    });

    // Set first label active
    changeLabel(labelButtons[0].id)
}

function sendDataForSave(task_id, image_id) {
    // Create a new canvas to put segmentation in
    var dummyCanvas = document.createElement('canvas');
    dummyCanvas.setAttribute('width', canvasWidth);
    dummyCanvas.setAttribute('height', canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        dummyCanvas = G_vmlCanvasManager.initElement(dummyCanvas);
    }

    // Put segmentation into canvas
    var ctx = dummyCanvas.getContext('2d');
    ctx.putImageData(segmentation, 0, 0);
    var dataURL = dummyCanvas.toDataURL('image/png', 1); // Use png to compress image and save bandwidth

    return $.ajax({
        type: "POST",
        url: "/segmentation/save/",
        data: {
            image: dataURL,
            width: canvasWidth,
            height: canvasHeight,
            image_id: image_id,
            task_id: task_id,
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadSegmentation(image_sequence_id, frame_nr, task_id, image_id) {
    console.log('In segmentation load')

    backgroundImage = new Image();
    frameNr = frame_nr;
    backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    backgroundImage.onload = function() {
        canvasWidth = this.width;
        canvasHeight = this.height;
        setupSegmentation(task_id, image_id);
    };

}

function addClick(x, y, dragging) {
    segmentationChanged = true;
    //var label = labels[activeLabel];
    var color = currentColor;
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
            segmentationData[(currentX + currentY*canvasWidth)*4] = color.red;
            segmentationData[(currentX + currentY*canvasWidth)*4+1] = color.green;
            segmentationData[(currentX + currentY*canvasWidth)*4+2] = color.blue;
            imageData[(currentX + currentY*canvasWidth)*4] = color.red;
            imageData[(currentX + currentY*canvasWidth)*4+1] = color.green;
            imageData[(currentX + currentY*canvasWidth)*4+2] = color.blue;
            var position = {x: currentX, y: currentY};
        }
    }
}

function redraw(){
    context.putImageData(image, 0, 0);
}

function addLabelButton(label_id, red, green, blue) {
     var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue
    };
    labelButtons.push(labelButton);

    red = red.toString(16);
    if(red.length == 1) {
        red = "0" + red;
    }
    green = green.toString(16);
    if(green.length == 1) {
        green = "0" + green;
    }
    blue = blue.toString(16);
    if(blue.length == 1) {
        blue = "0" + blue;
    }
    $("#labelButton" + label_id).css("background-color", "#" + red + green + blue);
}

function changeLabel(label_id) {
    for(var i = 0; i < labelButtons.length; i++)  {
        if(labelButtons[i].id == label_id) {
            currentLabel = i;
            label = labelButtons[i]
            // Set correct button to active
            $('#labelButton' + label.id).addClass('activeLabel');
            currentColor = {
                red: label.red,
                green: label.green,
                blue: label.blue
            };
            console.log(i + ' is now active label');
        } else {
            // Set all other buttons to inactive
            $('#labelButton' + labelButtons[i].id).removeClass('activeLabel');
        }
    }
}


// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
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
