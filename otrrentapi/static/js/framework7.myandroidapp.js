// Initialize your app
// ---------------------------------------------------------------------------------------
var myApp = new Framework7({

    material: true, //enable Material theme

    // If it is webapp, we can enable hash navigation:
    pushState: true,

    //swipe panel
    swipePanel: true,
    swipePanelCloseOpposite: true,

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

    //callback on submit push element to send settings in POST request 
    $$('.ajax-submit').on('submitted', function (e) {

        myApp.showIndicator();
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

        myApp.hideIndicator();
    });

});



