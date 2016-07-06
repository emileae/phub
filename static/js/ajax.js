$("body").on("submit", "#contact_form", function(e){

  e.preventDefault();
  var name = $("#enquiry_name").val();
  var email = $("#enquiry_email").val();
  var description = $("#enquiry_description").val();
  var web = $("#enquiry_web").val();
  var mobile = $("#enquiry_mobile").val();
  var game = $("#enquiry_game").val();

  function success(data){
    $("#enquiry_name").val("");
    $("#enquiry_email").val("");
    $("#enquiry_email").removeClass("valid");
    $("#enquiry_description").val("");
    $("#enquiry_web").prop("checked", false);
    $("#enquiry_mobile").prop("checked", false);
    $("#enquiry_game").prop("checked", false);

    $("#thank_you").css("height", "4rem");
  };

  $.ajax({
    url: "/contact",
    type: "post",
    data: {
      "enquiry_name": name, 
      "enquiry_email": email,
      "enquiry_description": description, 
      "enquiry_web": web,
      "enquiry_mobile": mobile, 
      "enquiry_game": game,
    },
    success: success
  });

});

$("body").on("submit", "#mailing_list_form", function(e){
  
  e.preventDefault();
  var name = $("#subscriber_name").val();
  var email = $("#subscriber_email").val();

  function success(data){
    $("#subscriber_name").val("");
    $("#subscriber_email").val("");
    $("#subscriber_email").removeClass("valid");

    $("#thank_you_subscribe").css("height", "4rem");
  };

  $.ajax({
    url: "/subscribe",
    type: "post",
    data: {
      "name": name, 
      "email": email,
    },
    success: success
  });

});

$("body").on("submit", "#unsubscribe_form", function(e){
  
  e.preventDefault();
  var email = $("#subscriber_email").val();

  console.log("ajax 1");

  function success(data){
    console.log("ajax 2");
    $("#subscriber_email").val("");
    $("#subscriber_email").removeClass("valid");

    $("#thank_you_unsubscribe").css("height", "4rem");
  };

  $.ajax({
    url: "/unsubscribe",
    type: "post",
    data: {
      "email": email,
    },
    success: success
  });

});