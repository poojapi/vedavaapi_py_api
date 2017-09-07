'use strict';

var api_url_base = "https://api.vedavaapi.org/py/";
if (window.location.href.includes("localhost")) {
    api_url_base = "http://localhost:9000";
}

function serialize(obj){
    var k = Object.keys(obj);
    var s = "";
    for(var i=0;i<k.length;i++) {
        //console.log(k[i] + "->" + obj[k[i]]);
        s += k[i] + "=" + encodeURIComponent(obj[k[i]]);
        if (i != k.length -1) s += "&";
    }
    return s;
};

// Makes an anchor tag.
function get_anchor_tag(lpath, text, newwin)
{
    if (typeof text == "undefined")
        text = lpath;
    if (typeof newwin == "undefined")
        newwin = true
    if (newwin == true)
        newwin = "target=\"_blank\"";
    var url = "";
    if (lpath.startsWith('http') || lpath.startsWith('/'))
        url = lpath;
    else url = api_url_base + "/textract/relpath/" + lpath;
    return '<a href="' + url + '" ' + newwin + '>' + text + '</a>';
}

//this method is for getting  serverinfo using api
function getServerInfo() {
}

function getFormParams(formname, fieldname_filter)
{
    var form_params = {};
    var myform = document.forms[formname];
    for (i=0; i < myform.elements.length; i++) {
        var fname = myform.elements[i].name;
        if (fieldname_filter !== undefined && 
                (fname.match(fieldname_filter) != null)){
            continue;
        }
        if (myform.elements[i].type == 'select-multiple') {
            var name = myform.elements[i].name;
            var $select = $('#' + name);
            var vals = [];
            $('#' + name + ' :selected').each(function() {
                vals.push($(this).val());
            });
            form_params[name] = vals;
        }
        //added code for checkbox value
        else if(myform.elements[i].type=="checkbox") {
            if($(myform.elements[i]).is(":checked")) {
                var name = myform.elements[i].name;
				if(name!="") {
					var $select = $('[name=' + name+'][type=checkbox]');
					form_params[name] = $select.val();
				}
            }
        }
        else if (myform.elements[i].type != 'button') {
            form_params[myform.elements[i].name] = myform.elements[i].value;
        } 
    }
    return form_params;
}

function getEpochTimeFromDateString(d) {
	var t = new Date(d);
	return d.getTime()/1000;
}
			
function getDateFromEpochTime(t,isUTC) {
	var utcSeconds = t;
	var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
	if(isUTC) {
		utcSeconds = utcSeconds + d.getTimezoneOffset()*60
	}
	d.setUTCSeconds(utcSeconds);
	return d;
}
