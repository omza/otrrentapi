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