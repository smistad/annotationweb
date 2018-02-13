var g_backgroundImageData;
var g_imageData;
var g_image;
var g_backgroundImage;
var g_frameNr;
var g_currentColor = null;
var g_controlPoints = [];
var g_move = false;
var g_pointToMove = -1;
var g_labelToMove = -1;
var g_moveDistanceThreshold = 8;
var g_drawLine = false;
var g_currentSegmentationLabel = 0;
var g_frameED = -1;
var g_frameES = -1;
var g_currentPhase = -1; // -1 == None, 0 == ED, 1 == ES
var g_shiftKeyPressed = false;

function setupLandmarkAnnotation() {

    // Initialize canvas with background image
    g_context.clearRect(0, 0, g_context.canvas.width, g_context.canvas.height); // Clears the canvas
    g_context.drawImage(g_backgroundImage, 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
    g_backgroundImageData = g_context.getImageData(0,0,g_canvasWidth, g_canvasHeight).data; // Get pixel data
    // Create the image which will be put on canvas
    g_image = g_context.getImageData(0, 0, g_canvasWidth, g_canvasHeight);
    g_imageData = g_image.data;

    // Remove any previous event handlers
    $('#canvas').off();

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            // Move point
            g_move = true;
            g_pointToMove = point.index;
            g_labelToMove = point.label;
        } else if(g_currentPhase >= 0) {
            if (g_controlPoints[g_currentPhase][g_currentSegmentationLabel].length<1)
            {
                addControlPoint(mouseX, mouseY, g_currentSegmentationLabel, g_currentPhase, g_shiftKeyPressed);
                if (g_currentSegmentationLabel<2){
                    changeLabel(g_currentSegmentationLabel+1);
                } else if(g_currentSegmentationLabel==2 && g_currentPhase==0) {
                    changeLabel(0);
                    goToFrame(g_frameES);
                }
            } else{
                console.log('Finished adding landmarks.')
            }
        }
        redrawSequence();
    });

    $('#canvas').mousemove(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var cursor = 'default';
        if(g_move && g_currentPhase >= 0) {
            cursor = 'move';
            setControlPoint(g_pointToMove, g_labelToMove, mouseX, mouseY);
            redrawSequence();
        } else {
            if(g_currentPhase >= 0) {
                cursor = 'pointer';
                g_drawLine = false;
                redrawSequence();
            }
        }
        $('#canvas').css({'cursor' : cursor});
        e.preventDefault();
    });

    $('#canvas').mouseup(function(e) {
        g_move = false;
    });

    $('#canvas').mouseleave(function(e) {
        g_drawLine = false;
        redrawSequence();
    });

    $('#canvas').dblclick(function(e) {
        if(g_move || g_currentPhase == -1)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            g_controlPoints[g_currentPhase][point.label].splice(point.index, 1);
        }
        redrawSequence();
    });

    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        if(g_currentPhase >= 0) {
            g_controlPoints[g_currentPhase][g_currentSegmentationLabel] = [];
        }
        redrawSequence();
    });

    $('#markAsED').click(function() {
        markED(g_currentFrameNr, g_framesLoaded);
        redrawSequence();
    });

    $('#markAsES').click(function() {
        markES(g_currentFrameNr, g_framesLoaded);
        redrawSequence();
    });

    $('#segmentED').click(function() {
        changeLabel(0);
        goToFrame(g_frameED);
    });

    $('#segmentES').click(function() {
        changeLabel(0);
        goToFrame(g_frameES);
    });

    $(document).on('keyup keydown', function(event) {
        g_shiftKeyPressed = event.shiftKey;
    });

    // Set first label active
    changeLabel(0);
    if(g_frameED >= 0)
        goToFrame(g_frameED);
    redraw();
}

function markED(frame, totalNrOfFrames) {
    g_frameED = frame;
    $('#sliderEDmark').css('background-color', '#CC3434');
    $('#sliderEDmark').css('width', $('.ui-slider-handle').css('width'));
    $('#sliderEDmark').css('margin-left', $('.ui-slider-handle').css('margin-left'));
    $('#sliderEDmark').css('height', '100%');
    $('#sliderEDmark').css('z-index', '99');
    $('#sliderEDmark').css('left', ''+(100.0*(frame+1)/totalNrOfFrames)+'%');
    $('#sliderEDmark').css('position', 'absolute');
    $('#EDFrame').text(g_frameED);
    console.log('Frame ED set to ' + g_frameED);
}

function markES(frame, totalNrOfFrames) {
    g_frameES = frame;
    $('#sliderESmark').css('background-color', '#0077b3');
    $('#sliderESmark').css('width', $('.ui-slider-handle').css('width'));
    $('#sliderESmark').css('margin-left', $('.ui-slider-handle').css('margin-left'));
    $('#sliderESmark').css('height', '100%');
    $('#sliderESmark').css('z-index', '99');
    $('#sliderESmark').css('left', ''+(100.0*(frame+1)/totalNrOfFrames)+'%');
    $('#sliderESmark').css('position', 'absolute');
    $('#ESFrame').text(g_frameES);
    console.log('Frame ES set to ' + g_frameES);
}

function loadLandmarkTask(image_sequence_id, frame_nr) {
    g_controlPoints.push([]); // ED
    g_controlPoints.push([]); // ES
    g_controlPoints[0].push([]); // Endo
    g_controlPoints[0].push([]); // Epi
    g_controlPoints[0].push([]); // Atrium
    g_controlPoints[1].push([]); // Endo
    g_controlPoints[1].push([]); // Epi
    g_controlPoints[1].push([]); // Atrium

    g_backgroundImage = new Image();
    g_frameNr = frame_nr;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupLandmarkAnnotation();
    };

}

function getClosestPoint(x, y) {
    if(g_currentPhase == -1)
        return false;
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;
    var minLabel = -1;

    for(var label = 0; label < 3; label++) {
        for(var i = 0; i < g_controlPoints[g_currentPhase][label].length; i++) {
            var point = getControlPoint(i, label);
            var distance = Math.sqrt((point.x - x) * (point.x - x) + (point.y - y) * (point.y - y));
            if(distance < minDistance) {
                minPoint = i;
                minDistance = distance;
                minLabel = label;
            }
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return {index: minPoint, label: minLabel};
    } else {
        return false;
    }
}

function createControlPoint(x, y, label, uncertain) {
    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == label) {
            labelIndex = i;
            break;
        }
    }

    var controlPoint = {
        x: x,
        y: y,
        label_id: label, // actual DB id
        label: labelIndex, // index: only used for color
        uncertain: uncertain    // whether the user is uncertain about this point or not
    };
    return controlPoint;
}

function addControlPoint(x, y, label, phase, uncertain) {
    var controlPoint = createControlPoint(x, y, label, uncertain);
    g_controlPoints[phase][label].push(controlPoint);
}

function getControlPoint(index, label) {
    if(index === -1) {
        index = g_controlPoints[g_currentPhase][label].length-1;
    }
    return g_controlPoints[g_currentPhase][label][index];
}

function setControlPoint(index, label, x, y) {
    g_controlPoints[g_currentPhase][label][index].x = x;
    g_controlPoints[g_currentPhase][label][index].y = y;

}

function redraw(){
    if(g_currentPhase == -1)
        return;

    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    var controlPointSize = g_canvasWidth/50;
    g_context.lineWidth = 2;

    // Draw controlPoint
    for(var labelIndex = 0; labelIndex < 3; labelIndex++) {
        for (var i = 0; i < g_controlPoints[g_currentPhase][labelIndex].length; ++i) {
            g_context.beginPath();

            var b = getControlPoint(i, labelIndex);
            var label = getLabelWithId(labelIndex);

            // Draw control point
            g_context.fillStyle = colorToHexString(label.red, label.green, label.blue);
            g_context.fillRect(b.x - controlPointSize / 2, b.y - controlPointSize / 2, controlPointSize, controlPointSize);
        }
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    if(g_currentFrameNr == g_frameED) {
        g_currentPhase = 0;
    } else if(g_currentFrameNr == g_frameES) {
        g_currentPhase = 1;
    } else {
        g_currentPhase = -1;
        var index = g_currentFrameNr - g_startFrame;
        g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    }
    redraw();
}

// Override of annotationweb.js
function changeLabel(label_id) {
    console.log('changing label to: ', label_id)
    g_currentSegmentationLabel = label_id;
    $('.labelButton').removeClass('activeLabel');
    $('#labelButton' + label_id).addClass('activeLabel');
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/cardiac_landmark/cardiac_landmark/save/",
        data: {
            control_points: JSON.stringify(g_controlPoints),
            frame_ed: g_frameED,
            frame_es: g_frameES,
            width: g_canvasWidth,
            height: g_canvasHeight,
            image_id: g_imageID,
            task_id: g_taskID,
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}
