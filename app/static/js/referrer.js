add_referrer = function(url, get_providers = false) {
    if (url.includes('?'))  { var conn = '&' } else { var conn = '?' };
    var new_url = url.concat(conn, 'ref_scroll=', window.scrollY);
    if (get_providers == true) {
        new_url = new_url.concat('&ref_providers=', getActivatedFilters().join(','))
    }
    return new_url;
};

add_referrer_and_load = function(url, get_providers = false) {
    window.location.href = add_referrer(url, get_providers);
};
