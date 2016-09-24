// Create the agent.
create_agent = function () {
    reqwest({
        url: "/node/" + participant_id,
        method: 'post',
        type: 'json',
        success: function (resp) {
            my_node_id = resp.node.id;
            console.log(my_node_id);
            $("#stimulus").show();
            $("#response-form").show();
            $("#send-message").removeClass('disabled');
            $("#send-message").html('Send');
            $("#reproduction").focus();
            setInterval(function () { get_transmissions(my_node_id); }, 2000);
        },
        error: function (err) {
            console.log(err);
            errorResponse = JSON.parse(err.response);
            if (errorResponse.hasOwnProperty('html')) {
                $('body').html(errorResponse.html);
            } else {
                allow_exit();
                go_to_page('questionnaire');
            }
        }
    });
};

get_transmissions = function (my_node_id) {
    reqwest({
        url: "/node/" + my_node_id + "/transmissions",
        method: 'get',
        type: 'json',
        data: {
            status: "pending",
        },
        success: function (resp) {
            console.log(resp);
            transmissions = resp.transmissions;
            for (var i = transmissions.length - 1; i >= 0; i--) {
                console.log(transmissions[i]);
                display_info(transmissions[i].info_id);
            }
        },
        error: function (err) {
            console.log(err);
            errorResponse = JSON.parse(err.response);
            $('body').html(errorResponse.html);
        }
    });
};

display_info = function(info_id) {
    reqwest({
        url: "/info/" + my_node_id + "/" + info_id,
        method: 'get',
        type: 'json',
        success: function (resp) {
            console.log(resp.info.contents);
            $("#story").append("<p>" + resp.info.contents + "</p>");
        },
        error: function (err) {
            console.log(err);
            errorResponse = JSON.parse(err.response);
            $('body').html(errorResponse.html);
        }
    });
};

send_message = function() {
    $("#send-message").addClass('disabled');
    $("#send-message").html('Sending...');

    response = $("#reproduction").val();
    $("#reproduction").val("");
    $("#story").append("<p style='color: #1693A5;'>" + response + "</p>");
    $("#reproduction").focus();

    reqwest({
        url: "/info/" + my_node_id,
        method: 'post',
        data: {
            contents: response,
            info_type: "Info",
        },
        success: function (resp) {
            console.log("sent!");
            $("#send-message").removeClass('disabled');
            $("#send-message").html('Send');
        }
    });
};

submit_response = function() {
    allow_exit();
    go_to_page('questionnaire');
};

$(document).keypress(function (e) {
  if (e.which == 13) {
    console.log("enter!");
    $("#send-message").click();
    return false;
  }
});

getQuorum = function () {
    reqwest({
        url: "/experiment/quorum",
        method: 'get',
        success: function (resp) {
            quorum = resp.quorum;
        }
    });
};

waitForQuorum = function () {
    reqwest({
        url: "/summary",
        method: 'get',
        success: function (resp) {
            summary = resp.summary;
            if (numReady(resp.summary) >= quorum) {
                go_to_page('exp');
            } else {
                waitForQuorum();
            }
        }
    });
};

numReady = function(summary) {
    for (var i = 0; i < summary.length; i++) {
        if (summary[i][0] == "working") {
            return summary[i][1];
        }
    }
};
