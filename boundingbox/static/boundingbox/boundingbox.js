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
var g_move = false;
var g_resize = false;
var g_invalidBoxNr = 999999;
var g_currentBox = g_invalidBoxNr;
var g_cornerSize = 20;

function setupSegmentation() {
    console.log('setting up segmentation....');

    // Define event callbacks
    $('#canvas').mousedown(function(e) {

        // TODO check if current frame is not the frame to segment
        var pos = mousePos(e, this);
        g_BBx = pos.x;
        g_BBy = pos.y;
        var insideBox = isInsideBox(pos.x, pos.y);
        if(insideBox.isInside) {
            g_currentBox = insideBox.boxNr
            if(insideBox.isInsideCorner)
                g_resize = true;
            else
                g_move = true;
            return;
        }
        g_paint = true;
        console.log('started BB on ' + g_BBx + ' ' + g_BBy);
    });

    $('#canvas').mousemove(function(e) {
        var pos = mousePos(e, this);
        if(g_paint) {
            g_BBx2 = pos.x;
            g_BBy2 = pos.y;
            redrawSequence();
            return;
        }

        //Position diff since last mouse position
        var xDiff = pos.x - g_BBx;
        var yDiff = pos.y - g_BBy;

        //Update initial position while moving or resizing.
        g_BBx = pos.x;
        g_BBy = pos.y;

        if(g_move) {
            moveBox(g_currentBox, xDiff, yDiff);
            return;
        }
        if(g_resize) {
            resizeBox(g_currentBox, xDiff, yDiff);
            return;
        }
    });

    $('#canvas').mouseup(function(e){
        g_move = false;
        g_resize = false;
        if(!g_paint)
            return;
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

    $('#canvas').dblclick(function(e){
        var pos = mousePos(e, this);
        insideBox = isInsideBox(pos.x, pos.y);
        if(insideBox.isInside)
            removeBox(insideBox.boxNr);
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

function isInsideBox(x, y) {
    var boxNr = g_invalidBoxNr;
    var isInside = false;
    var isInsideCorner = false;

    if(g_currentFrameNr in g_boxes) {
        for(var i = 0; i < g_boxes[g_currentFrameNr].length; ++i) {
            var box = g_boxes[g_currentFrameNr][i];
            if(((x >= box.x) && (x <= (box.x+box.width))) && ((y >= box.y) && (y <= (box.y+box.height))) ) {
                isInside = true;
                if(!isInsideCorner)
                    boxNr = i;//Don't change boxnr if we are inside the corner of another box
                if((x >= (box.x+box.width-g_cornerSize)) && (y >= (box.y+box.height-g_cornerSize)))//Lower right
                    isInsideCorner = true;
            }
        }
    }
//    console.log('isInside: ' + isInside + ' ' + boxNr)
    return {
        isInside: isInside,
        boxNr: boxNr,
        isInsideCorner: isInsideCorner,
    };
}

function removeBox(boxNr)
{
    console.log('removeBox: ' + boxNr);
    var removedBox = g_boxes[g_currentFrameNr].splice(boxNr, 1);
    g_annotationHasChanged = true;
    redrawSequence();
}

function moveBox(boxNr, xDiff, yDiff)
{
    box = g_boxes[g_currentFrameNr][boxNr];
    box.x += xDiff;
    box.y += yDiff;
    redrawSequence();
}

function resizeBox(boxNr, xDiff, yDiff)
{
    box = g_boxes[g_currentFrameNr][boxNr];
    if(box.width > (-xDiff + g_minimumSize))
        box.width += xDiff;
    if(box.height > (-yDiff + g_minimumSize))
    box.height += yDiff;
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
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + 0 + '/' + g_taskID + '/';
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

    // Draw all stored boxes
    for(var i = 0; i < g_boxes[g_currentFrameNr].length; ++i) {
        g_context.beginPath();
        g_context.lineWidth = 2;
        box = g_boxes[g_currentFrameNr][i];
        label = g_labelButtons[box.label];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        g_context.rect(box.x, box.y, box.width, box.height);
        g_context.moveTo(box.x+box.width-g_cornerSize, box.y+box.height);
        g_context.lineTo(box.x+box.width, box.y+box.height-g_cornerSize);
        g_context.stroke();
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();
}

function copyToNext() {
    // TODO: Check content of g_boxes[g_currentFrameNr+1] -> Is it empty/exist? Overwrite?
    if (g_currentFrameNr < g_sequenceLength + 1) {
        var boxes_to_copy = g_boxes[g_currentFrameNr];
        for (var i = 0; i < boxes_to_copy.length; i++) {
            addBox(g_currentFrameNr + 1, boxes_to_copy[i].x, boxes_to_copy[i].y,
                boxes_to_copy[i].x + boxes_to_copy[i].width,
                boxes_to_copy[i].y + boxes_to_copy[i].height,
                boxes_to_copy[i].label_id);
        }
        //console.log(boxes_to_copy)
        // Uncomment the next two lines if you want a confirmation message.
        // Note that this message will stay until the site is refreshed
        // var messageBox = document.getElementById("message");
        // messageBox.innerHTML = '<span class="info">Content copied to the next frame!</span>';
    }
}
