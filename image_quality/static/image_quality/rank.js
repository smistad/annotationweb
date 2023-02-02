let g_rankings = {}; // rankings dictionary [key_frame_nr] contains a dictionary/map of objects with a dictionary
let g_categories = []; // list of category id's


function setupRanking(categories) {
    g_categories = categories;
    $('#addFrameButton').click(function() {
        g_rankings[g_currentFrameNr] = {}
        g_categories.forEach((id) => {
            console.log('category ids', id);
            g_rankings[g_currentFrameNr][id] = -1;
        });
        redrawSequence();
    });
}

function updateRanking(category_id, element) {
    if(!(g_currentFrameNr in g_rankings)) {
        return;
    }
    console.log(category_id, element.value);
    g_rankings[g_currentFrameNr][category_id] = element.value;
    console.log($(element).find(":selected").attr('data-color'));
    $(element).css('background-color', $(element).find(":selected").attr('data-color'));
}

function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image

    if(!(g_currentFrameNr in g_rankings)) {
        $(".rank-select").prop("disabled", true);
          $(".rank-select").each(function() {
            $(this).val("-1");
            $(this).css("background-color", "grey");
        });
    } else {
        $(".rank-select").prop("disabled", false);
        // Populate form with values of this frame
        $(".rank-select").each(function() {
            //console.log($(this).attr("data-id"));
            let currentValue = g_rankings[g_currentFrameNr][parseInt($(this).attr("data-id"))];
            if(currentValue === undefined) {
                $(this).val("-1");
                $(this).css("background-color", "white");
            } else {
                //console.log('current value', currentValue);
                $(this).val(currentValue);
                $(this).css("background-color", $(this).find(":selected").attr("data-color"));
            }
        });
    }
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/image-quality/save/",
        data: {
            rankings: JSON.stringify(g_rankings),
            target_frames: JSON.stringify(g_targetFrames),
            image_id: g_imageID,
            task_id: g_taskID,
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
            quality: 'ok',
        },
        dataType: "json" // Need this do get result back as JSON
    });
}
