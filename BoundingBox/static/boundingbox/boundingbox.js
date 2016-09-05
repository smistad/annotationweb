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
        addBox();
        console.log('finished BB on ' + BBx + ' ' + BBy);
        //segmentationHistory.push(currentAction); // Add action to history
    });

    $('#canvas').mouseleave(function(e){
        if(paint) {
            addBox();
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
                messageBox.innerHTML = '<span class="error">Save failed!</span>';
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

function createBox() {
    // Select the one closest to 0,0
    var boxOriginX = min(BBx, BBx2);
    var boxOriginY = min(BBy, BBy2);

    // Calculate width and height
    var width = max(BBx, BBx2) - boxOriginX;
    var height = max(BBy, BBy2) - boxOriginY;

    var box = {
        x: boxOriginX,
        y: boxOriginY,
        width: width,
        height: height,
        label_id: labelButtons[currentLabel].id, // actual DB id
        label: currentLabel // index: only used for color
    };
    return box;
}

function addBox() {

    var box = createBox();
    boxes.push(box);
}

function sendDataForSave(task_id, image_id) {
    return $.ajax({
        type: "POST",
        url: "/boundingbox/save/",
        data: {
            image_id: image_id,
            boxes: JSON.stringify(boxes),
            task_id: task_id,
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadBBTask(image_sequence_id, frame_nr, task_id, image_id) {
    console.log('In bb task load')

    backgroundImage = new Image();
    frameNr = frame_nr;
    backgroundImage.src = '/annotation/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
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
        var box = createBox();
        var label = labelButtons[box.label];
        context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        context.rect(box.x, box.y, box.width, box.height);
        context.stroke();
    }
}

function colorToHexString(red, green, blue) {
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
    return '#' + red + green + blue;
}

function addLabelButton(label_id, red, green, blue) {
    var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue
    };
    labelButtons.push(labelButton);


    console.log(red + green + blue);
    $("#labelButton" + label_id).css("background-color", colorToHexString(red, green, blue));
}

function changeLabel(label_id) {
    for(var i = 0; i < labelButtons.length; i++)  {
        if(labelButtons[i].id == label_id) {
            currentLabel = i;
            var label = labelButtons[i]
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
