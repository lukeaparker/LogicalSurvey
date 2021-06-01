$(document).ready(function (){
    var stripe = Stripe('pk_test_51Hc5nMKz33UhW15YsXA6U8h9Selq7p1O0DlHPLtaTxBVr6FVVRJq3d8pJ4NIZKC9JGWLUet32mSFj8KgHrCi9ccG00etKhT7DU');
  
    var checkoutButton = document.getElementById('checkout-button-price_1HqVhHKz33UhW15YXeBBEBm5');
    checkoutButton.addEventListener('click', function () {
      // When the customer clicks on the button, redirect
      // them to Checkout.
      stripe.redirectToCheckout({
        lineItems: [{price: 'price_1HqVhHKz33UhW15YXeBBEBm5', quantity: 1}],
        mode: 'payment',
        // Do not rely on the redirect to the successUrl for fulfilling
        // purchases, customers may not always reach the success_url after
        // a successful payment.
        // Instead use one of the strategies described in
        // https://stripe.com/docs/payments/checkout/fulfill-orders
        successUrl: 'https://your-website.com/success',
        cancelUrl: 'https://your-website.com/canceled',
      })
      .then(function (result) {
        if (result.error) {
          // If `redirectToCheckout` fails due to a browser or network
          // error, display the localized error message to your customer.
          var displayError = document.getElementById('error-message');
          displayError.textContent = result.error.message;
        }
      });
    });
    $("#referrals").on("change keyup paste", () => {
        document.querySelector(".err-msg").innerHTML = ""
    });

    $(".referral-submit").on("click", event => {
        event.preventDefault();
        var mailFormat = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        var emailSet = new Set();
        var err = "";

        emails = $("#referrals").val();
        splitEmails = emails.split(",");
        
        splitEmails.forEach((email, i) => {
            email = email.trim()
            splitEmails[i] = email
            emailSet.add(email)

            if (!mailFormat.test(email)) {
                err = "Please input valid emails!"
            } 
        });
        
        if (splitEmails.length != emailSet.size) {
            err += "<br>Please use unique emails!"
        } else if (splitEmails.length != 10) {
            err += "<br>You must input 10 emails!"
        }

        if (err != "") {
            document.querySelector(".err-msg").innerHTML = err;
        } else {
            document.querySelector(".referral-submit").innerHTML += `<div class="spinner-border spinner-border-sm" role="status" style="margin-left:4px;"><span class="sr-only">Loading...</span></div>`
            $.ajax({
                type: "POST",
                url: "http://localhost:5000/send-referrals",
                data: $("form").serialize()
            }).then(response => {
                if (response.success == false) {
                    err = "Could not verify all of the emails! <ul style='margin-left: 17px;'>"
                    response.failed.forEach(fail => {
                        err += "<li>" + fail + "</li>"
                    })
                    err += "</ul>"

                    document.querySelector(".err-msg").innerHTML = err;
                    document.querySelector(".referral-submit").innerHTML = "Send Referrals"
                } else if (response.success == true) {
                    window.location.href = "/questionnaire/success"
                }
            })
        }
    });
});

(function() {
    
  })();