var g_context;
var g_canvasWidth = 512;
var g_canvasHeight = 512;
var g_sequence = [];
var g_labelButtons = [];
var g_currentFrameNr;
var g_startFrame;
var g_progressbar;
var g_framesLoaded;
var g_isPlaying = true;
var g_returnURL = '';
var g_taskID;
var g_imageID;
var g_currentLabel = -1;
// Set this true if user has changed annotation. This will trigger a dialog
// if user press next or previous
var g_annotationHasChanged = false;
var g_nextURL = '';

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
    $('#slider').slider('value', g_currentFrameNr); // Update slider
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

function save() {
    var messageBox = document.getElementById("message")
    messageBox.innerHTML = '<span class="info">Please wait while saving..</span>';
    sendDataForSave().done(function(data) {
        console.log("Save done..");
        console.log(data);
        var messageBox = document.getElementById("message")
        if(data.success == "true") {
            messageBox.innerHTML = '<span class="success">Image was saved</span>';
            if(g_returnURL != '') {
                window.location = g_returnURL;
            } else {
                // Reset image quality form before refreshing
                $('#imageQualityForm')[0].reset();
                // Refresh page
                location.reload();
            }
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

function loadSequence(image_sequence_id, nrOfFrames, target_frame, show_entire_sequence, images_to_load_before, images_to_load_after, auto_play) {
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

    g_currentFrameNr = target_frame;

    var start;
    var end;
    var totalToLoad;
    if(show_entire_sequence) {
        start = 0;
        end = nrOfFrames-1;
        totalToLoad = nrOfFrames;
    } else {
        start = max(0, target_frame - images_to_load_before);
        end = min(nrOfFrames - 1, target_frame + images_to_load_after);
        totalToLoad = end - start;
    }
    g_startFrame = start;

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
            if(g_isPlaying)
                incrementFrame();
      }
    });

    $("#addFrameButton").click(function() {
        $("#framesSelected").append('<li>' + g_currentFrameNr + '</li>');
        $("#framesForm").append('<input type="hidden" name="frames" value="' + g_currentFrameNr + '">');
    });

    $("#goToTargetFrame").click(function() {
        setPlayButton(false);
        g_currentFrameNr = target_frame;
        $('#slider').slider('value', target_frame); // Update slider
        redrawSequence();
    });


    // Load images
    g_framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for(var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/show_frame/' + image_sequence_id + '/' + i + '/';
        image.onload = function() {
            g_canvasWidth = this.width;
            g_canvasHeight = this.height;
            canvas.setAttribute('width', g_canvasWidth);
            canvas.setAttribute('height', g_canvasHeight);

            // Update progressbar
            g_framesLoaded++;
            g_progressbar.progressbar( "value", g_framesLoaded*100/totalToLoad);
        }

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

function addLabelButton(label_id, red, green, blue) {
    var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue
    };
    g_labelButtons.push(labelButton);

    $("#labelButton" + label_id).css("background-color", colorToHexString(red, green, blue));
}

function changeLabel(label_id) {
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].id == label_id) {
            g_currentLabel = label_id;
            var label = g_labelButtons[i]
            // Set correct button to active
            $('#labelButton' + label.id).addClass('activeLabel');
            g_currentColor = {
                red: label.red,
                green: label.green,
                blue: label.blue
            };
            console.log(i + ' is now active label');
        } else {
            // Set all other buttons to inactive
            $('#labelButton' + g_labelButtons[i].id).removeClass('activeLabel');
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
