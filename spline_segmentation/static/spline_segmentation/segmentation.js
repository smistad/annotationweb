var g_backgroundImage;
var g_currentColor = null;
var g_controlPoints = {}; // control point dictionary [key_frame_nr] contains a dictionary/map of objects with a dictionary with label: label data, control_points: list
var g_currentObject = 0; // Which index in g_controlPoints[key_frame_nr] list we are in
var g_move = false;
var g_pointToMove = -1;
var g_labelToMove = -1;
var g_moveDistanceThreshold = 8;
var g_drawLine = false;
var g_currentLabel = -1;

function getMaxObjectID() {
    var max = -1;
    for(var key in g_controlPoints[g_currentFrameNr]) {
        key = parseInt(key); // dictionary keys are strings
        if(key > max)
            max = key;
    }
    return max;
}

function setupSegmentation() {

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        if(e.ctrlKey && g_controlPoints[g_currentFrameNr][g_currentObject].control_points.length >= 3) { // Create new object if ctrl key is held down AND current object has more than 2 points
            g_currentObject = getMaxObjectID()+1;
            data = {label: g_labelButtons[g_currentLabel], control_points: []};
            g_controlPoints[g_currentFrameNr][g_currentObject] = data;
        }

        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            // Activate object of this point
            g_currentObject = point.object;
            $('.labelButton').removeClass('activeLabel');
            $('#labelButton' + point.label_idx).addClass('activeLabel');
            g_currentLabel = getLabelIdxWithId(point.label_idx);
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
                addControlPointsForNewFrame(g_currentFrameNr);
                // Add point at end
                addControlPoint(mouseX, mouseY, g_currentFrameNr, g_currentObject, g_labelButtons[g_currentLabel].id, g_shiftKeyPressed);
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
            setControlPoint(g_pointToMove, g_currentObject, mouseX, mouseY);
            redrawSequence();
        } else {
            if(!e.ctrlKey &&
                g_currentFrameNr in g_controlPoints &&
                g_currentObject in g_controlPoints[g_currentFrameNr] &&
                g_controlPoints[g_currentFrameNr][g_currentObject].control_points.length > 0 &&
                isPointOnSpline(mouseX, mouseY) < 0) {
                // If mouse is not close to spline, draw dotted drawing line
                var line = {
                    x0: getControlPoint(-1, g_currentObject).x,
                    y0: getControlPoint(-1, g_currentObject).y,
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

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        var scale =  g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft)*scale;
        var mouseY = (e.pageY - this.offsetTop)*scale;
        var point = getClosestPoint(mouseX, mouseY);
        if(point !== false) {
            g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(point.index, 1);
            //if(g_controlPoints[g_currentFrameNr[g_currentObject]].control_points.length == 0) {
            //    g_controlPoints[g_currentFrameNr].splice(g_currentObject, 1); // remove this object
            //}
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_controlPoints[g_currentFrameNr][g_currentObject].control_points = [];
        redrawSequence();
    });

    $('#removeFrameButton').click(function() {
        // Remove splines in this frame
        if(g_currentFrameNr in g_controlPoints){
            delete g_controlPoints[g_currentFrameNr];
        }
        redrawSequence();
    });

    $(document).keydown(function(event) {
       if(event.ctrlKey)  {
           g_drawLine = false;
           redrawSequence();
       }
    });

    $('#addFrameButton').click(function() {
        addControlPointsForNewFrame(g_currentFrameNr);
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id)

    redraw();
}

function addControlPointsForNewFrame(frameNr) {
    if(frameNr in g_controlPoints) // Already exists
        return;
    g_controlPoints[frameNr] = {};
}

function loadSegmentationTask(image_sequence_id) {

    g_backgroundImage = new Image();
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + 0 + '/' + g_taskID + '/';
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
    var minObject = -1;

    for(var j in g_controlPoints[g_currentFrameNr]) {
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][j].control_points.length; i++) {
            var point = getControlPoint(i, j);
            var distance = Math.sqrt((point.x - x) * (point.x - x) + (point.y - y) * (point.y - y));
            if(distance < minDistance) {
                minPoint = i;
                minDistance = distance;
                minLabel = g_controlPoints[g_currentFrameNr][j].label.id;
                minObject = j;
            }
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return {index: minPoint, label_idx: minLabel, object: minObject};
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
    g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(index+1, 0, controlPoint);
}

function addControlPoint(x, y, target_frame, object, label, uncertain) {
    var controlPoint = createControlPoint(x, y, label, uncertain);
    if(!(object in g_controlPoints[target_frame])) // add object if it doesn't exist
        g_controlPoints[target_frame][object] = {label: g_labelButtons[getLabelIdxWithId(label)], control_points: []};
    g_controlPoints[target_frame][object].control_points.push(controlPoint);
}

function getControlPoint(index, object) {
    if(index === -1) {
        index = g_controlPoints[g_currentFrameNr][object].control_points.length-1;
    }
    return g_controlPoints[g_currentFrameNr][object].control_points[index];
}

function setControlPoint(index, object, x, y) {
    g_controlPoints[g_currentFrameNr][object].control_points[index].x = x;
    g_controlPoints[g_currentFrameNr][object].control_points[index].y = y;
}

function isPointOnSpline(pointX, pointY) {
    for(var object in g_controlPoints[g_currentFrameNr]) {
        for (var i = 0; i < g_controlPoints[g_currentFrameNr][object].control_points.length; ++i) {
            var a = getControlPoint(max(0, i - 1), object);
            var b = getControlPoint(i, object);
            var c = getControlPoint(min(g_controlPoints[g_currentFrameNr][object].control_points.length - 1, i + 1), object);
            var d = getControlPoint(min(g_controlPoints[g_currentFrameNr][object].control_points.length - 1, i + 2), object);

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
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);

    if(!(g_currentFrameNr in g_controlPoints))
        return;

    var controlPointSize = 6;
    g_context.lineWidth = 2;

    // Draw controlPoint
    for(var j in g_controlPoints[g_currentFrameNr]) {
        var label = g_controlPoints[g_currentFrameNr][j].label;
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][j].control_points.length; i++) {
            g_context.beginPath();
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);

            // Draw line as spline

            var maxIndex = g_controlPoints[g_currentFrameNr][j].control_points.length;
            var first;
            if (i === 0) {
                first = maxIndex - 1;
            } else {
                first = i - 1;
            }

            var a = getControlPoint(first, j);
            var b = getControlPoint(i, j);
            var c = getControlPoint((i + 1) % maxIndex, j);
            var d = getControlPoint((i + 2) % maxIndex, j);

            var step = 0.1;
            var tension = 0.5;

            if (b.uncertain || c.uncertain) {
                // Draw uncertain segments with dashed line
                g_context.setLineDash([1, 5]); // dashes are 5px and spaces are 5px
            } else {
                g_context.setLineDash([]); // reset
            }

            var pointList = [a, b, c, d];
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
        if(g_labelButtons[i].id == id) {
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

    // changeLabel is called when we press the label button (may or may not have an object),
    // and when we press a control point (already have object)
    if(g_currentFrameNr in g_controlPoints) {
        var found = false;
        for(var j in g_controlPoints[g_currentFrameNr]) {
            if(g_controlPoints[g_currentFrameNr][j].label.id == label_id) {
                g_currentObject = j;
                found = true;
                break;
            }
        }
        if(!found) {
            // Create new object id
            g_currentObject = getMaxObjectID()+1;
            g_controlPoints[g_currentFrameNr][g_currentObject] = {label: g_labelButtons[getLabelIdxWithId(label)], control_points: []};
        }
    }
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
