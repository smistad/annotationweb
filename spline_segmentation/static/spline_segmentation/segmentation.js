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
var g_shiftKeyPressed = false;
var g_currentTargetFrameIdx = -1;
var g_currentLabel = -1;
var g_targetFrames = [];

function setupSegmentation() {

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
            g_labelToMove = point.label_idx;
        } else {
            var section = isPointOnSpline(mouseX, mouseY);
            if(section >= 0) {
                // Insert point
                insertControlPoint(mouseX, mouseY, g_labelButtons[g_currentLabel].id, section);
            } else {
                // Add point at end
                addControlPoint(mouseX, mouseY, g_currentTargetFrameIdx, g_labelButtons[g_currentLabel].id, g_shiftKeyPressed);
            }
        }
        redrawSequence();
    });

    $('#canvas').mousemove(function(e) {
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var cursor = 'default';


        if(g_move) {
            cursor = 'move';
            setControlPoint(g_pointToMove, g_labelToMove, mouseX, mouseY);
            redrawSequence();
        } else {
            if(g_controlPoints[g_currentLabel].length > 0 && isPointOnSpline(mouseX, mouseY) < 0) {
                // If mouse is not close to spline, draw dotted drawing line
                var line = {
                    x0: getControlPoint(-1, g_currentLabel).x,
                    y0: getControlPoint(-1, g_currentLabel).y,
                    x1: mouseX,
                    y1: mouseY
                };
                g_drawLine = line;
            } else {
                cursor = 'pointer';
                g_drawLine = false;
            }
            redrawSequence();
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

    var z = document.getElementById("canvas");
    var baseWidth = 500;
    var padding = 100;

    var zoomStep = 30;

    var handleWheel = function (event) {
        // cross-browser wheel delta
        // Chrome / IE: both are set to the same thing - WheelEvent for Chrome, MouseWheelEvent for IE
        // Firefox: first one is undefined, second one is MouseScrollEvent
        var e = window.event || event;
        // Chrome / IE: first one is +/-120 (positive on mouse up), second one is zero
        // Firefox: first one is undefined, second one is -/+3 (negative on mouse up)
        var delta = Math.max(-1, Math.min(1, e.wheelDelta || -e.detail));

        // Do something with `delta`
        console.log(z.clientWidth, padding, zoomStep, delta)
        var zz = z.clientWidth + zoomStep * delta;
        zz = Math.max(zoomStep, Math.min(2 * baseWidth, zz));
        console.log(zz)

        z.style.width = zz + "px";

        z.innerHTML = "<small>" + window.event + " | " + event +
          "</small><br><small>" +   e.wheelDelta + " | " + e.detail +
          "</small><br>" + delta + " | " + zz + " | " + z.clientWidth + "px";

        e.preventDefault();
    };

    $('#canvas').bind('mousewheel DOMMouseScroll', function(event){
        handleWheel(event);
    });

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            g_controlPoints[point.label_idx].splice(point.index, 1);
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_controlPoints = [];

        setupControlPointArray()
        redrawSequence();
    });

    $('#addTargetFrameButton').click(function() {
        goToFrame(g_currentFrameNr)
        setPlayButton(false);
        $('#slider').slider('value', g_currentFrameNr); // Update slider
        g_targetFrames.push(g_currentFrameNr)
        setupControlPointArray()
        markTargetFrame(g_currentFrameNr, g_framesLoaded);
        redrawSequence();
    });

    $('#removeTargetFrameButton').click(function() {
        goToFrame(g_currentFrameNr)
        setPlayButton(false);
        $('#slider').slider('value', g_currentFrameNr); // Update slider

        if(g_targetFrames.includes(g_currentFrameNr)){
            var target_frame_idx = g_targetFrames.indexOf(g_currentFrameNr)
            var target_id = "sliderMarker" + target_frame_idx

            slider.querySelector(target_id).remove();
            g_targetFrames.splice(target_frame_idx,1);
            g_controlPoints.splice(target_frame_idx,1);
        }


        redrawSequence();
    });

    var targetFrameIncrement = 0;
    $('#switchTargetFrameButton').click(function() {
        if(g_targetFrames.length>0){
            goToFrame(g_targetFrames[targetFrameIncrement%g_targetFrames.length]);
            targetFrameIncrement++;
            setPlayButton(false);
            $('#slider').slider('value', g_currentFrameNr); // Update slider
            redrawSequence();
        }
    });

    $(document).on('keyup keydown', function(event) {
        g_shiftKeyPressed = event.shiftKey;
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id)

    redraw();
}

function markTargetFrame(frame, totalNrOfFrames){
    g_currentTargetFrame = frame;
    setupSliderMark(frame, totalNrOfFrames);
    console.log('Target frame set to ' + g_currentTargetFrame);
}

function markTargetFrames(frames){
    for(var i=0; i<frames.length; i++){
        g_targetFrames.push(frames[i]);
        setupSliderMark(frames[i], g_sequenceLength);
    }
    setupControlPointArray()
}

function setupSliderMark(frame, totalNrOfFrames){
    marker_index = g_targetFrames.findIndex(index => index === frame)

    var slider = document.getElementById('slider')

    var newMarker = document.createElement("sliderMarker" + marker_index)
    $(newMarker).css('background-color', '#0077b3');
    $(newMarker).css('width', $('.ui-slider-handle').css('width'));
    $(newMarker).css('margin-left', $('.ui-slider-handle').css('margin-left'));
    $(newMarker).css('height', '100%');
    $(newMarker).css('z-index', '99');
    $(newMarker).css('position', 'absolute');
    $(newMarker).css('left', ''+(100.0*(frame-g_startFrame)/totalNrOfFrames)+'%');

    slider.appendChild(newMarker)
}

function setupControlPointArray(){
    if(g_controlPoints.length === 0) {
        for (var j = 0; j < g_labelButtons.length; j++) {
            g_controlPoints.push([]);
        }
    }
}

function loadSegmentationTask(image_sequence_id, frame_nr) {
    setupControlPointArray();

    g_backgroundImage = new Image();
    g_frameNr = frame_nr;
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + frame_nr + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupSegmentation();
    };
}

function getClosestPoint(x, y) {
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;
    var minLabel = -1;

    for(var label_idx = 0; label_idx < g_labelButtons.length; label_idx++) {
        for(var i = 0; i < g_controlPoints[label_idx].length; i++) {
            var point = getControlPoint(i, label_idx);
            var distance = Math.sqrt((point.x - x) * (point.x - x) + (point.y - y) * (point.y - y));
            if(distance < minDistance) {
                minPoint = i;
                minDistance = distance;
                minLabel = label_idx;
            }
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return {index: minPoint, label_idx: minLabel};
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

function insertControlPoint(x, y, label, index) {
    var controlPoint = createControlPoint(x, y, label, g_shiftKeyPressed);
    g_controlPoints[g_currentLabel].splice(index+1, 0, controlPoint);
}

function addControlPoint(x, y, target_frame, label, uncertain) {
    var controlPoint = createControlPoint(x, y, label, uncertain);
    g_controlPoints[controlPoint.label].push(controlPoint);
}

function getControlPoint(index, label) {
    if(index === -1) {
        index = g_controlPoints[label].length-1;
    }
    return g_controlPoints[label][index];
}

function setControlPoint(index, label, x, y) {
    g_controlPoints[label][index].x = x;
    g_controlPoints[label][index].y = y;
}

function isPointOnSpline(pointX, pointY) {
    for(var label = 0; label < g_labelButtons.length; label++) {
        for (var i = 0; i < g_controlPoints[label].length; ++i) {
            var a = getControlPoint(max(0, i - 1), label);
            var b = getControlPoint(i, label);
            var c = getControlPoint(min(g_controlPoints[label].length - 1, i + 1), label);
            var d = getControlPoint(min(g_controlPoints[label].length - 1, i + 2), label);

            var step = 0.1;
            var tension = 0.5;
            for (var t = 0.0; t < 1; t += step) {
                var x =
                    (2 * t * t * t - 3 * t * t + 1) * b.x +
                    (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.x - a.x) +
                    (-2 * t * t * t + 3 * t * t) * c.x +
                    (1 - tension) * (t * t * t - t * t) * (d.x - b.x);
                var y =
                    (2 * t * t * t - 3 * t * t + 1) * b.y +
                    (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.y - a.y) +
                    (-2 * t * t * t + 3 * t * t) * c.y +
                    (1 - tension) * (t * t * t - t * t) * (d.y - b.y);
                if (Math.sqrt((pointX - x) * (pointX - x) + (pointY - y) * (pointY - y)) < g_moveDistanceThreshold) {
                    return i;
                }
            }
        }
    }
    return -1;
}




function redraw(){
    //g_context.putImageData(g_image, 0, 0);
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);


    if(g_currentFrameNr != g_frameNr)
        return;

    var controlPointSize = 6;
    g_context.lineWidth = 2;

    // Draw controlPoint
    for(var labelIndex = 0; labelIndex < g_labelButtons.length; labelIndex++) {
        for (var i = 0; i < g_controlPoints[labelIndex].length; i++) {
            var label = g_labelButtons[labelIndex];

            g_context.beginPath();
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);

            // Draw line as spline

            var maxIndex = g_controlPoints[labelIndex].length;
            var first;
            if(i === 0) {
                first = maxIndex-1;
            } else {
                first = i-1;
            }

            var a = getControlPoint(first, labelIndex);
            var b = getControlPoint(i, labelIndex);
            var c = getControlPoint((i+1) % maxIndex, labelIndex);
            var d = getControlPoint((i+2) % maxIndex, labelIndex);

            var step = 0.1;
            var tension = 0.5;

            if(b.uncertain || c.uncertain) {
                // Draw uncertain segments with dashed line
                g_context.setLineDash([1, 5]); // dashes are 5px and spaces are 5px
            } else {
                g_context.setLineDash([]); // reset
            }

            var pointList = [a,b,c,d];
            drawSpline(pointList, step, tension)

            // Draw control point
            g_context.fillStyle = colorToHexString(255, 255, 0);
            g_context.fillRect(b.x - controlPointSize / 2, b.y - controlPointSize / 2, controlPointSize, controlPointSize);
        }

        /*
        // Draw spline between end points
        if(g_controlPoints[labelIndex].length > 4) {
                var a = getControlPoint(g_controlPoints[labelIndex].length-2, labelIndex);
                var b = getControlPoint(g_controlPoints[labelIndex].length-1, labelIndex);
                var c = getControlPoint(0, labelIndex);
                var d = getControlPoint(1, labelIndex);

                var pointList = [a,b,c,d];
                drawSpline(pointList, step, tension);
        }*/
    }

    if(g_drawLine !== false) {
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        var label = g_labelButtons[g_currentLabel];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        g_context.moveTo(g_drawLine.x0, g_drawLine.y0);
        g_context.lineTo(g_drawLine.x1, g_drawLine.y1);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();
}

function getLabelIdxWithId(id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if (g_labelButtons[i].id == id) {
            return i;
        }
    }
}

// Override of annotationweb.js
function changeLabel(label_id) {
    console.log('changing label to: ', label_id)
    $('.labelButton').removeClass('activeLabel');
    $('#labelButton' + label_id).addClass('activeLabel');
    g_currentLabel = getLabelIdxWithId(label_id);
}

function drawSpline(pointList, step_size, tension){
    var a = pointList[0];
    var b = pointList[1];
    var c = pointList[2];
    var d = pointList[3];

    prev_x = -1;
    prev_y = -1;

    for(var t = 0.0; t < 1; t += step_size) {
        var x = (2 * t * t * t - 3 * t * t + 1) * b.x +
                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.x - a.x) +
                (-2 * t * t * t + 3 * t * t) * c.x +
                (1 - tension) * (t * t * t - t * t) * (d.x - b.x);
        var y = (2 * t * t * t - 3 * t * t + 1) * b.y +
                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.y - a.y) +
                (-2 * t * t * t + 3 * t * t) * c.y +
                (1 - tension) * (t * t * t - t * t) * (d.y - b.y);

        // Draw line
        if(prev_x >= 0) {
            g_context.moveTo(prev_x, prev_y);
            g_context.lineTo(x, y);
            g_context.stroke();
        }
        prev_x = x;
        prev_y = y;
    }
}


function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/spline-segmentation/save/",
        data: {
            control_points: JSON.stringify(g_controlPoints),
            target_frames: JSON.stringify(g_targetFrames),
            n_labels: g_labelButtons.length,
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
