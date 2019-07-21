add_referrer = function(url, current_title) {
    if (url.includes('?'))  { var conn = '&' } else { var conn = '?' }
    var new_url = url.concat(conn, 'ref=', current_title, '&ref_scroll=', window.scrollY)
    window.location.href = new_url
};
