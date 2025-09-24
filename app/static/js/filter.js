// Switch filter state and apply filtering
function switchFilterState(p) {
  var x;
  x = document.getElementsByClassName(p)[0];
  if (x.className.includes('OFF')) {
    x.className = x.className.replace('OFF', 'ON');
  }
  else {
    x.className = x.className.replace('ON', 'OFF');
  }
  filterSelection();
}

// Provide activated filters list
function getActivatedFilters() {
  const p = ["netflix", "amazonprimevideo", "canal", "disneyplus", "mubi", "universcine", "plex"];
  var x = [], y, i;
  for (i = 0; i < p.length; i++) {
    y = document.getElementsByClassName(p[i]);
    if (y.length > 0) {
        y = y[0];
        if (y.className.includes("ON")) {
          x.push(p[i])
        };
    };
  }
  return x;
}

// Filter out all elements not matching the activated filter(s)
function filterSelection() {
  var x, y, i, j, k;
  x = document.getElementsByClassName("filterDiv");
  y = getActivatedFilters()
  var visibleCount = 0;
  for (i = 0; i < x.length; i++) {
    k = false
    addClass(x[i], "show");
    for (j = 0; j < y.length; j++) {
      if (x[i].className.includes(y[j])) k = true;
    }
    if (y.length > 0 & k == false) {
      removeClass(x[i], "show");
    } else {
      visibleCount++;
    }
  }
  updateMovieCount(visibleCount, y.length > 0, x.length);
};

// Show filtered elements
function addClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {
      element.className += " " + arr2[i];
    }
  }
}

// Hide elements that are not selected
function removeClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);
    }
  }
  element.className = arr1.join(" ");
}

// Add function to update the movie count display
function updateMovieCount(visible, filtered, total) {
  var el = document.getElementById("movie-count");
  if (!el) return;
  if (filtered) {
    el.textContent = visible + " movie" + (visible === 1 ? "" : "s") + " selected";
  } else {
    el.textContent = total + " movie" + (total === 1 ? "" : "s") + " in total";
  }
}
