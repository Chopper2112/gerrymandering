function addNumCommas(num) {
  num = num+""
  newNum = num[num.length-1]
  i = 0
  for(let c = num.length-2; c >= 0; c--) {
    i++
    if(i % 3 == 0) {
      newNum = ","+newNum
    }
    newNum = num[c]+newNum
  }
  return newNum
}

// https://codepen.io/KryptoniteDove/post/load-json-file-locally-using-pure-javascript
function loadJSON(filename, callback) {
  var xobj = new XMLHttpRequest();
  xobj.overrideMimeType("application/json");
  xobj.open('GET', filename, true); 
  xobj.onreadystatechange = function () {
    if (xobj.readyState == 4 && xobj.status == "200") {
      callback(xobj.responseText);
    }
  };
  xobj.send(null);
}

states = {
  'VA': {'lat': 37.83, 'lng': -79.45, 'zoom': 6.85 }
}

state = 'VA'
stateLat = states[state]['lat']
stateLng = states[state]['lng']
stateZoom = states[state]['zoom']
partyColor = {"Republican": "red", "Democratic": "blue"}

// Apply state data
function loadStateMap(map) {
 
  // Center and zoom map on state
  map.setCenter({lat:stateLat, lng:stateLng});
  map.setZoom(stateZoom);

  // Load districts overlay
  loadJSON('geodata.json', function(response) {
    geodata = JSON.parse(response)
    features = map.data.addGeoJson(geodata)

    // Set color of district based on party
    features.forEach(feature => {
      districtID = parseInt(feature.getProperty("SLDLST"))+""
      map.data.overrideStyle(feature, {fillColor:partyColor[data["districts"][districtID]["winner"]]})
    })
  })

  // Style overlay
  map.data.setStyle({
    strokeColor: 'black',
    fillOpacity: 0.5,
    strokeWeight: 1,
  });  
}

// Create map
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    mapId: '4f69a9ead9eb85cc',
    center: {lat:stateLat, lng:stateLng},
    zoom: stateZoom,
    disableDefaultUI: true,
    zoomControl: false,
    minZoom: stateZoom,
    maxZoom: stateZoom+6,
    gestureHandling: 'cooperating', //set to none to disable zooming/panning
    restriction: {
      latLngBounds: {
        north: stateLat+3,
        south: stateLat-3,
        east: stateLng+5,
        west: stateLng-5,
      },
    },
  });
}

function loadPage(state, election) {
  data = null

  // Load election information from json
  loadJSON('output/'+state+'/'+election+'.json', function(response) {
    data = JSON.parse(response)

    // Create webpage
    document.getElementById("state").innerHTML = data["metadata"]["state"].toUpperCase()
    document.getElementById("chamber").innerHTML = data["metadata"]["chamber"] +" &mdash; "+ data["metadata"]["year"]

    // Set gerrymandering rating
    gerrymander_rating = '0'
    // gerrymander_rating = data["gerrymandering"]["score"].toFixed(2)
    document.getElementById("gerrymander_rating").innerHTML = gerrymander_rating
    if(gerrymander_rating < 1) { document.getElementById("gerrymander_rating").style.color = "lime" }
    else if(gerrymander_rating < 5) { document.getElementById("gerrymander_rating").style.color = "yellow" }
    else if(gerrymander_rating >= 5) { document.getElementById("gerrymander_rating").style.color = "red" }

    // Create votes bar
    document.getElementById("r_segment").style.width = data["votes"]["Republican_%"]+"%"
    document.getElementById("d_segment").style.width = data["votes"]["Democratic_%"]+"%"
    document.getElementById("o_segment").style.width = data["votes"]["Other_%"]+"%"
    document.getElementById("r_votes").innerHTML = data["votes"]["Republican_%"]+"% &mdash; "+addNumCommas(data["votes"]["Republican"])
    document.getElementById("d_votes").innerHTML = data["votes"]["Democratic_%"]+"% &mdash; "+addNumCommas(data["votes"]["Democratic"])
    if(data["votes"]["Other_%"] > 5) { document.getElementById("o_segment").innerHTML = "OTHER" }

    // Create seats graphics
    templateSeat = document.createElement('img')
    templateSeat.style.width = "5%"
    templateSeat.style.height = "5%"
    templateSeat.style.visibility = "hidden"
    document.getElementById("r_seats").innerHTML = "Republican: "+data["seats"]["Republican"]
    document.getElementById("d_seats").innerHTML = "Democratic: "+data["seats"]["Democratic"]

    seat = 0
    maxSeats = data["seats"]["total"]
    seatsPerRow = 20
    seatRows = maxSeats/seatsPerRow

    // Create rows
    for(let i = 1; i < seatRows; i++) {
      var newRow = document.getElementById("seat_row_0").cloneNode(true);
      newRow.id = "seat_row_"+i
      document.getElementById('seats').appendChild(newRow);
    }
    var row = document.getElementById('seat_row_0')

    // Create icons
    for(let i = 0; i < maxSeats; i++) {
      
      // Advance to next row if needed
      if(seat % seatsPerRow == 0) {
        row = document.getElementById('seat_row_'+(seat/seatsPerRow))
      }
      seat++;

      // Create icon
      var newSeat = templateSeat.cloneNode(true);

      if(i < data["seats"]["Republican"]) { newSeat.src = "lib/red.png" }
      else if(i-data["seats"]["Republican"] < data["seats"]["Democratic"]) { newSeat.src = "lib/blue.png" }
      else { newSeat.src = "lib/gray.png" }

      newSeat.style.visibility = "visible"

      row.appendChild(newSeat);
    }

    // Create population infobox
    document.getElementById("voted_pop_label").innerHTML = "VOTED IN "+data["metadata"]["year"]+'<div class="population_number" id="voted_pop"></div>'
    document.getElementById("total_pop").innerHTML = addNumCommas(data["population"])
    document.getElementById("voted_pop").innerHTML = addNumCommas(data["votes"]["total"])
    document.getElementById("vote_turnout").innerHTML = data["voter_turnout_%"]+"%"
    document.getElementById("avg_pop").innerHTML = addNumCommas(data["avg_population"])

    // Make page visible
    document.getElementById("main").style.display = "block"

  })

  return data
}

election = window.location.href.substring(window.location.href.indexOf("#/")+5)
state = window.location.href.substring(window.location.href.indexOf("#/")+2,window.location.href.indexOf("#/")+4)

// Change page if different election is selected
window.onhashchange = function() { 
  election = window.location.href.substring(window.location.href.indexOf("#/")+5)
  state = window.location.href.substring(window.location.href.indexOf("#/")+2,window.location.href.indexOf("#/")+4)
  location.reload()
}

// Load state map
window.onload = function() {
  loadStateMap(map);
}

// Load page
data = loadPage(state, election)