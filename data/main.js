// ***
// This function shows or hides all modules in a release that are
// 100% translated
// ***
function showHideCompleted() {
    var regex = /complete$/i;

    var doc = document.getElementById("documentation");
    if (doc) {
        var translations = doc.getElementsByTagName("tr");

        for(var i=0;i<translations.length;i++) {
            if ( regex.exec(translations[i].id) ) {
                if ( translations[i].style.display != 'none' ) {
                    translations[i].style.display = 'none';
                }
                else {
                    translations[i].style.display = '';
                }
            }
	    }
	}
	
    var ui = document.getElementById("user-interface");
    var translations = ui.getElementsByTagName("tr");

    for(var i=0;i<translations.length;i++) {
        if ( regex.exec(translations[i].id) ) {
            if ( translations[i].style.display != 'none' ) {
                translations[i].style.display = 'none';
            }
            else {
                translations[i].style.display = '';
            }
        }
    }
    
    var hide = document.getElementById("hide");
    var show = document.getElementById("show");

    hide.style.display = (hide.style.display != 'none' ? 'none' : '' );
    show.style.display = (show.style.display != 'none' ? 'none' : '' );
    return false;
}
