// Login with ClientID and Device Fingerprint
// --------------------------------------------------------------------------------------
function OtrrentAuth() {
    // otrentauth constructor

    // attributes
    this.ClientID = localStorage.getItem('ClientID') === null ? '' : localStorage.getItem('ClientID');
    this.Fingerprint = localStorage.getItem('Fingerprint') === null ? '' : localStorage.getItem('Fingerprint');
    this.LoggedIn = false;
    this.SessionTimeout = 0;

    //get a hash, representing your device fingerprint
    if (this.Fingerprint === '') {
        var self = this;
        new Fingerprint2().get(function (result) {
            self.Fingerprint = result;
            self.login();
        });
    } else {
        this.login();
    }

    // method to login
    this.login = function () {

        // invoke push REST API call to login or create new user or get client ID
        // pure js !
        if (window.XMLHttpRequest) {
            // code for modern browsers
            xhttp = new XMLHttpRequest();
        } else {
            // code for old IE browsers
            xhttp = new ActiveXObject("Microsoft.XMLHTTP");
        }

        // async callback success/error
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4 && this.status === 200) {

                // write item in history
                objResponse = JSON.parse(this.response);

                this.ClientID = objResponse.ClientId; //a hash, representing your Client ID
                localStorage.setItem('ClientID', objResponse.ClientId);

                this.LoggedIn = objResponse.LoggedIn;
                this.SessionTimeout = objResponse.SessionTimeout;

            }
        };

        // invoke ajax call
        var url = window.location.origin + '/api/user/login';
        xhttp.open("POST", url, true);

        //set headers
        xhttp.setRequestHeader("dataType", "json");
        xhttp.setRequestHeader("Content-type", "application/json; charset=utf-8");

        // send data
        var PostJson = {
            "ClientID": this.ClientID,
            "Fingerprint": this.Fingerprint
        };
        xhttp.send(JSON.stringify(PostJson));

    };
}

var Authentification = new OtrrentAuth();

// Initialize your app
// ---------------------------------------------------------------------------------------
var myApp = new Framework7({

    material: true, //enable Material theme

    // If it is webapp, we can enable hash navigation:
    pushState: true,

    // Hide and show indicator during ajax requests
    onAjaxStart: function (xhr) {
        myApp.showIndicator();
    },
    onAjaxComplete: function (xhr) {
        myApp.hideIndicator();
    }
}); 

// Export selectors engine
var $$ = Dom7;

// Add view
var mainView = myApp.addView('.view-main', {
    // Because we use fixed-through navbar we can enable dynamic navbar
    //dynamicNavbar: true
});

// Callbacks to run specific code for specific pages, for example for About page:
myApp.onPageInit('details', function (page) {
    // run createContentPage func after link was clicked

    //callback on submit show Indicator 
    $$('.ajax-submit').on('submit', function (e) {
        myApp.showIndicator();
    });

    //callback on submit push element to send settings in POST request 
    $$('.ajax-submit').on('submitted', function (e) {
        var xhr = e.detail.xhr; // actual XHR object
        var responsePage = xhr.responseText; //response data

        //Load new content as new page
        mainView.router.reloadContent(responsePage);
        myApp.hideIndicator();
    });

});

// Callbacks for Settings page
myApp.onPageInit('settings', function (page) {

    //callback after submit settings form
    $$('.ajax-submit-onchange').on('submitted', function (e) {
        var xhr = e.detail.xhr; // actual XHR object
        var responsePage = xhr.responseText; //response data

        //get focused element in form
        var focusedId = document.activeElement.id;

        //Load new content as new page
        mainView.router.reloadContent(responsePage);

        //set focus
        if (typeof focusedId !== 'undefined' && focusedId !== null && focusedId !== "") {
            var focusedEl = document.getElementById(focusedId);
            focusedEl.focus();

            if (focusedEl.type === 'textarea') {
                focusedEl.setSelectionRange(focusedEl.value.length, focusedEl.value.length);
            }
            
        }
        
    });

});



