var g_targetLabels = {}; // dictionary [target_frame_nr] contains a dictionary/map of frames with corresponding label

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/classification/save/",
        data: {
            image_id: g_imageID,
            task_id: g_taskID,
            label_id: g_currentLabel,
            target_frames: JSON.stringify(g_targetFrames),
            target_labels: JSON.stringify(g_targetLabels),
            quality: $('input[name=quality]:checked').val(),
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadClassificationTask() {

    $('#clearButton').click(function() {
        g_annotationHasChanged = true;
        // Reset image quality form
        $('#imageQualityForm input[type="radio"]').each(function(){
            $(this).prop('checked', false);
        });
        // Set all label buttons to inactive
        changeLabel(-1);
    });

    $('#removeFrameButton').click(function() {
        var frame = parseInt(g_currentFrameNr);
        delete g_targetLabels[frame];
        g_targetFrames = g_targetFrames.filter(function (value, index, arr) {return value!=frame});
        updateSliderMarks();
        });

    // Add click listener for label buttons to trigger save if annotating whole sequence with one label
    if(!g_annotateIndividualFrames){
        for(var i = 0; i < g_labelButtons.length; ++i) {
            var label_id = g_labelButtons[i].id;
            $('#labelButton' + label_id).click(function() {
                // Only trigger save if label has no children
                var childrenFound = false;
                for(var j = 0; j < g_labelButtons.length; j++) {
                    var child_label = g_labelButtons[j];
                    if(child_label.parent_id == g_currentLabel) {
                        childrenFound = true;
                    } else if(child_label.parent_id != 0) {
                    }
                }
                if(!childrenFound)
                    save();
            });
        }
    }

    $('#addFrameButton').click(function() {
        addLabelsForNewFrame(g_currentFrameNr);
    });

    // Overload of progressbar complete in annotationweb.js
    $('#progressbar').progressbar({
        complete: function () {
            $(".progress-label").text( "Finished loading!" );
            g_progressbar.hide();
            redrawSequence();

            updateSliderMarks();

            if(g_isPlaying)
                incrementFrame();
        }
    });
}

function addLabelsForNewFrame(frameNr) {
    if(frameNr in g_targetLabels) // Already exists
        return;
    g_targetLabels[frameNr] = {};
}



// Overload of annotationweb.js implementation of updateSlideMarks
function updateSliderMarks(){
    removeAllSliderMarks();

    for(var label_nr in g_targetLabels){
        var label = g_targetLabels[label_nr]
        var color = colorToHexString(label.label.red, label.label.green, label.label.blue)
        setupSliderMark(label_nr, g_framesLoaded, color);
    }
}

function loadLabels(target_frame, label_id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if (g_labelButtons[i].id == label_id) {
            var label = g_labelButtons[i];
            g_targetLabels[target_frame] = {label: label};
            break;
        }
    }
}

// Override of annotationweb.js
function changeLabel(label_id) {
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].id == label_id) {

            // Hide previous label's sublabels and show new ones
            var labelList = getLabelList(g_labelButtons[i]);
            showLabelList(labelList);

            g_currentLabel = label_id;
            var label = g_labelButtons[i];

            // Set correct button to active
            if(!g_annotateIndividualFrames)
                decorateLabelButtons(labelList);

            g_currentColor = {red: label.red, green: label.green, blue: label.blue};

            console.log(i + ' is now active label for frame ' + g_currentFrameNr);
            g_targetLabels[g_currentFrameNr] = {label: label};
            break;
        }
    }

    updateSliderMarks();
}