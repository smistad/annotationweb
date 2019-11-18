var g_context;
var g_canvasWidth = 512;
var g_canvasHeight = 512;
var g_sequence = [];
var g_labelButtons = [];
var g_currentFrameNr; // The frame nr currently displayed
var g_startFrame;
var g_progressbar;
var g_framesLoaded;
var g_sequenceLength;
var g_isPlaying = true;
var g_returnURL = '';
var g_taskID;
var g_imageID;
var g_currentLabel = -1;
// Set this true if user has changed annotation. This will trigger a dialog
// if user press next or previous
var g_annotationHasChanged = false;
var g_nextURL = '';
var g_rejected = false;
var g_targetFrames = []; // Frames to annotate
var g_currentTargetFrameIndex = -1; // Index of current target frame (g_targetFrames), -1 if not on target frame

function max(a, b) {
    return a > b ? a : b;
}

function min(a, b) {
    return a < b ? a : b;
}

function incrementFrame() {
    if(!g_isPlaying) // If this is set to false, stop playing
        return;
    g_currentFrameNr = ((g_currentFrameNr-g_startFrame) + 1) % g_framesLoaded + g_startFrame;
    var marker_index = g_targetFrames.findIndex(index => index === g_currentFrameNr);
    if(marker_index) {
        g_currentTargetFrameIndex = g_currentFrameNr;
    } else {
        g_currentTargetFrameIndex = -1;
    }
    $('#slider').slider('value', g_currentFrameNr); // Update slider
    $('#currentFrame').text(g_currentFrameNr);
    redrawSequence();
    window.setTimeout(incrementFrame, 50);
}

function setPlayButton(play) {
    g_isPlaying = play;
    if(g_isPlaying) {
        $("#playButton").html('Pause');
    } else {
        $("#playButton").html('Play');
    }
}

function goToFrame(frameNr) {
    setPlayButton(false);
    g_currentFrameNr = frameNr;
    $('#slider').slider('value', frameNr); // Update slider
    var marker_index = g_targetFrames.findIndex(index => index === frameNr);
    if(marker_index) {
        g_currentTargetFrameIndex = g_currentFrameNr;
    } else {
        g_currentTargetFrameIndex = -1;
    }
    redrawSequence();
}

function save() {
    var messageBox = document.getElementById("message");
    messageBox.innerHTML = '<span class="info">Please wait while saving..</span>';
    sendDataForSave().done(function(data) {
        console.log("Save done..");
        console.log(data);
        var messageBox = document.getElementById("message");
        if(data.success == "true") {
            messageBox.innerHTML = '<span class="success">Image was saved</span>';
            if(g_returnURL != '') {
                window.location = g_returnURL;
            } else {
                // Reset image quality form before refreshing
                $('#imageQualityForm')[0].reset();
                $('#comments').val('');
                // Refresh page
                location.reload();
            }
        } else {
            messageBox.innerHTML = '<div class="error"><strong>Save failed!</strong><br> ' + data.message + '</div>';
        }
        console.log(data.message);
    }).fail(function(data) {
        console.log("Ajax failed");
        var messageBox = document.getElementById("message");
        messageBox.innerHTML = '<span class="error">Save failed!</span>';
    }).always(function(data) {
        console.log("Ajax complete");
    });
    console.log("Save function executed");
}

function initializeAnnotation(taskID, imageID) {
    g_taskID = taskID;
    g_imageID = imageID;

    // This is required due to djangos CSRF protection
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Setup save button
    $('#saveButton').click(save);

    // If reject is selected, mark as rejected, then save
    $('#rejectButton').click(function() {
        g_rejected = true;
        save();
    });

    $('#imageQualityForm input[type="radio"]').change(function(){
        g_annotationHasChanged = true;
    });

    // Create dialog
    $("#dialogConfirm").dialog({
          resizable: false,
          height: "auto",
          width: 400,
          modal: true,
            autoOpen: false,
          buttons: {
            "Save and go to next/previous": function() {
              $( this ).dialog( "close" );
                g_returnURL = g_nextURL;
                save();
            },
            "Discard changes and go to next/previous": function() {
              $( this ).dialog( "close" );
                window.location.href = g_nextURL;
            },
            Cancel: function() {
              $( this ).dialog( "close" );
            },
          }
        });
}

function setupSliderMark(frame, totalNrOfFrames){
    var marker_index = g_targetFrames.findIndex(index => index === frame);

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

function loadSequence(image_sequence_id, start_frame, nrOfFrames, show_entire_sequence, user_frame_selection, annotate_single_frame, frames_to_annotate, images_to_load_before, images_to_load_after, auto_play) {
    g_targetFrames = frames_to_annotate;
    g_targetFrames.sort(function(a, b){return a-b});

    console.log('In load sequence');
    // Create play/pause button
    setPlayButton(auto_play);
    $("#playButton").click(function() {
        setPlayButton(!g_isPlaying);
        if(g_isPlaying) // Start it again
            incrementFrame();
    });

    // Create canvas
    var canvas = document.getElementById('canvas');
    canvas.setAttribute('width', g_canvasWidth);
    canvas.setAttribute('height', g_canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    g_context = canvas.getContext("2d");

    if(g_targetFrames.length > 0) {
        g_currentFrameNr = g_targetFrames[0];
    } else {
        g_currentFrameNr = 0;
    }

    var start;
    var end;
    var totalToLoad;
    if(show_entire_sequence || !annotate_single_frame) {
        start = start_frame;
        end = start_frame + nrOfFrames - 1;
        totalToLoad = nrOfFrames;
    } else {
        start = max(start_frame, g_currentFrameNr - images_to_load_before);
        end = min(start_frame + nrOfFrames - 1, g_currentFrameNr + images_to_load_after);
        totalToLoad = end - start;
    }
    g_startFrame = start;
    g_sequenceLength = end-start;

    // Create slider
    $("#slider").slider(
            {
                range: "max",
                min: start,
                max: end,
                step: 1,
                value: g_currentFrameNr,
            slide: function(event, ui) {
                g_currentFrameNr = ui.value;
                $('#currentFrame').text(g_currentFrameNr);
                setPlayButton(false);
                redrawSequence();
            }
            }
    );

    // Create progress bar
    g_progressbar = $( "#progressbar" );
    var progressLabel = $(".progress-label");
    g_progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( "Please wait while loading. " + g_progressbar.progressbar( "value" ).toFixed(1) + "%" );
      },
      complete: function() {
            // Remove progress bar and redraw
            progressLabel.text( "Finished loading!" );
            g_progressbar.hide();
            redrawSequence();
            for(var i = 0; i < g_targetFrames.length; i++) {
                setupSliderMark(g_targetFrames[i], nrOfFrames);
            }
            if(g_isPlaying)
                incrementFrame();
      }
    });

    $("#addFrameButton").click(function() {
        setPlayButton(false);
        if(g_targetFrames.includes(g_currentFrameNr)) // Already exists
            return;
        setupSliderMark(g_currentFrameNr, g_framesLoaded);
        g_targetFrames.push(g_currentFrameNr);
        g_currentTargetFrameIndex = g_targetFrames.length-1;
        g_targetFrames.sort(function(a, b){return a-b});
        $("#framesSelected").append('<li>' + g_currentFrameNr + '</li>');
        $("#framesForm").append('<input type="hidden" name="frames" value="' + g_currentFrameNr + '">');
    });

    $("#nextFrameButton").click(function() {
        // Find next frame
        var i;
        if(g_targetFrames[g_targetFrames.length-1] <= g_currentFrameNr) {
            i = 0;
        } else {
            for (i = 0; i < g_targetFrames.length; i++) {
                if(g_targetFrames[i] > g_currentFrameNr)
                    break;
            }
        }
        g_currentTargetFrameIndex = i;
        goToFrame(g_targetFrames[i]);
    });

    $("#canvas").click(function() {
        // Stop playing if user clicks image
        setPlayButton(false);
        //g_currentFrameNr = target_frame;
        //$('#slider').slider('value', target_frame); // Update slider
        redrawSequence();
    });

    // Load images
    g_framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for(var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/show_frame/' + image_sequence_id + '/' + i + '/' + g_taskID + '/';
        image.onload = function() {
            g_canvasWidth = this.width;
            g_canvasHeight = this.height;
            canvas.setAttribute('width', g_canvasWidth);
            canvas.setAttribute('height', g_canvasHeight);

            // Update progressbar
            g_framesLoaded++;
            g_progressbar.progressbar( "value", g_framesLoaded*100/totalToLoad);
        };
        g_sequence.push(image);
    }
}

function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
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

function setReturnURL(url) {
    g_returnURL = url;
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

function addLabelButton(label_id, red, green, blue, parent_id) {
    var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue,
        parent_id: parent_id,
    };
    g_labelButtons.push(labelButton);

    $("#labelButton" + label_id).css("background-color", colorToHexString(red, green, blue));

    // TODO finish
    if(parent_id != 0) {
        $('#sublabel_' + parent_id).hide();
    }
}

function getLabelWithId(id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if (g_labelButtons[i].id == id) {
            return g_labelButtons[i];
        }
    }
}

function getLabelList(label) {
    var currentLabel = label;
    var labels = [];
    labels.push(label);
    while(currentLabel.parent_id != 0) {
        currentLabel = getLabelWithId(currentLabel.parent_id);
        labels.push(currentLabel);
    }

    return labels;
}

function showLabelList(list) {
    // Hide all sublabel groups first
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].parent_id != 0) {
            $('#sublabel_' + g_labelButtons[i].parent_id).hide();
        }
    }
    // Then show the ones needed
    for(var i = 0; i < list.length; i++) {
        console.log("Showing sublabel group " + list[i].id);
        $('#sublabel_' + list[i].id).show();
    }
}

function decorateLabelButtons(list) {
    // Remove active class from all first
    for(var i = 0; i < g_labelButtons.length; i++)  {
        $('#labelButton' + g_labelButtons[i].id).removeClass('activeLabel');
    }
    // Then add it the ones which have been selected
    for(var i = 0; i < list.length; i++) {
        $('#labelButton' + list[i].id).addClass('activeLabel');
    }
}

function changeLabel(label_id) {
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].id == label_id) {
            // Hide previous label's sublabels
            var labelList = getLabelList(g_labelButtons[i]);
            showLabelList(labelList);

            g_currentLabel = label_id;
            // Show new label's sublabels

            var label = g_labelButtons[i];
            // Set correct button to active
            decorateLabelButtons(labelList);
            //$('#labelButton' + label.id).addClass('activeLabel');
            g_currentColor = {
                red: label.red,
                green: label.green,
                blue: label.blue
            };
            console.log(i + ' is now active label');
            break;
        }
    }
}

function changeImage(url) {
    if(g_annotationHasChanged) {
        // Open dialog
        g_nextURL = url;
        $('#dialogConfirm').dialog("open");
    } else {
        window.location.href = url;
    }
}
