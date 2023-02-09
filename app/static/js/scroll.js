add_scroll = function(url) {
    if (url.includes('?'))  { var conn = '&' } else { var conn = '?' };
    return url.concat(conn, 'scroll_to=', window.scrollY);
};

add_scroll_and_load = function(url, get_providers = false) {
    window.location.href = add_scroll(url, get_providers);
};
