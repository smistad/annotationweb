var g_backgroundImageData;
var g_imageData;
var g_image;
var g_backgroundImage;
var g_frameNr;
var g_currentColor = null;
var g_landmarks = {}; // Dictionary with keys frame_nr which each has a list of landmarks

function setupLandmarkTask() {
    console.log("Setting up canvas task..");

    // Define event callbacks
    $('#canvas').click(function(e) {
        var pos = mousePos(e, this);
        if(!g_shiftKeyPressed) {
            // Check if frame is a key frame
            console.log(g_userFrameSelection);
            if(g_userFrameSelection) {
                if(!g_targetFrames.includes(g_currentFrameNr)) {
                    setPlayButton(false);
                    addKeyFrame(g_currentFrameNr);
                    g_landmarks[g_currentFrameNr] = [];
                }
            }
            if(g_targetFrames.includes(g_currentFrameNr)) {
                console.log("adding landmark..");
                // Check if already exists
                let exists = false;
                for(let i = 0; i < g_landmarks[g_currentFrameNr].length; ++i) {
                    let landmark = g_landmarks[g_currentFrameNr][i];
                    if(landmark.label_id === g_currentLabel && Math.abs(pos.x - landmark.x) < 6 && Math.abs(pos.y - landmark.y) < 6) {
                        exists = true;
                    }
                }
                if(!exists)
                    addLandmark(pos.x, pos.y, g_currentLabel, g_currentFrameNr);
            }
        } else {
            console.log("deleting landmark..");
            let frameNr = g_currentFrameNr;
            if(frameNr in g_landmarks) {
                for(let i = 0; i < g_landmarks[frameNr].length; ++i) {
                    let landmark = g_landmarks[frameNr][i];
                    console.log('Testing..');
                    if(Math.abs(pos.x - landmark.x) < 8 && Math.abs(pos.y - landmark.y) < 8) {
                        console.log('Deleting landmark..');
                        // Delete it
                        g_landmarks[frameNr].splice(i, 1);
                        break;
                    }
                }
            }
        }
        redrawSequence();
    });

    $("#addFrameButton").click(function() {
        g_landmarks[g_currentFrameNr] = [];
    });

    $('#removeFrameButton').click(function() {
        // Remove landmarks in this frame
        if(g_currentFrameNr in g_landmarks){
            delete g_landmarks[g_currentFrameNr];
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        // Clear all annotations for the current label and frame

        // Find label index
        var labelText = $("#labelButton" + g_currentLabel).text();
        if(confirm("Are you sure you wish to delete all landmarks of type " + labelText + " for ALL frames?")) {
            g_annotationHasChanged = true;
            for (var frame in g_landmarks) {
                g_landmarks[frame] = g_landmarks[frame].filter(function (value, index, arr) {
                    return value.label_id != g_currentLabel;
                });
            }
            redrawSequence();
        }
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id);
    redraw();
}

function createLandmark(x, y, label) {
    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == label) {
            labelIndex = i;
            break;
        }
    }

    var landmark = {
        x: x,
        y: y,
        label_id: label, // actual DB id
        label: labelIndex // index: only used for color
    };
    return landmark;
}

function addLandmark(x, y, label, frameNr) {
    var landmark = createLandmark(x, y, label);
    if(frameNr in g_landmarks) {
        g_landmarks[frameNr].push(landmark);
    } else {
        g_landmarks[frameNr] = [landmark];
    }
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/landmark/save/",
        data: {
            image_id: g_imageID,
            landmarks: JSON.stringify(g_landmarks),
            task_id: g_taskID,
            target_frames: JSON.stringify(g_targetFrames),
            quality: $('input[name=quality]:checked').val(),
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadLandmarkTask(image_sequence_id) {
    console.log('In landmark task load')

    g_backgroundImage = new Image();
    g_backgroundImage.src = '/show_frame/' + image_sequence_id + '/' + 0 + '/' + g_taskID + '/';
    g_backgroundImage.onload = function() {
        g_canvasWidth = this.width;
        g_canvasHeight = this.height;
        setupLandmarkTask();
    };

}

function redraw() {
    var landmarkSize = 20;
    // Draw all stores landmarks
    if(g_currentFrameNr in g_landmarks) {
        for(var i = 0; i < g_landmarks[g_currentFrameNr].length; ++i) {
            g_context.beginPath();
            g_context.lineWidth = 3;
            var landmark = g_landmarks[g_currentFrameNr][i];
            var label = g_labelButtons[landmark.label];
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
            var y = landmark.y;
            var x = landmark.x;
            var start_x = landmark.x - landmarkSize / 2;
            var start_y = landmark.y - landmarkSize / 2;
            var end_x = landmark.x + landmarkSize / 2;
            var end_y = landmark.y + landmarkSize / 2;
            // Horizontal line
            g_context.moveTo(start_x, y);
            g_context.lineTo(end_x, y);
            // Vertical line
            g_context.moveTo(x, start_y);
            g_context.lineTo(x, end_y);
            g_context.stroke();
        }
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();
}
