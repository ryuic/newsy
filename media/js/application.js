function toggle(e){
  var id = e.id.match('navi-(.+)')[1];
  if(this.previous_id == id){ return false; }
  this.previous_id = id;

  $('a', $('#navi')).each(function(){
    this.className = (this == e) ?'selected': 'unselect';
  });

  $('.thing').each(function(){
    if(this.id == id){
      $(this).show('fast');
    }else{
      $(this).hide('fast');
    }
  });
  return false;
}
function load(url){
  var script = document.createElement("script");
  script.setAttribute("type", "text/javascript");
  script.setAttribute("charset", "utf-8");
  script.setAttribute("src", url);
  document.body.appendChild(script);
}

$(document).ready(function(){
  if(keywords == ''){ return false; }
  if(!$('#video')){ return false; }

  var url = 'http://gdata.youtube.com/feeds/videos?' +
      'vq=' + encodeURIComponent(keywords) + '&' +
      'alt=json-in-script&' +
      'max-results=10&' +
      'callback=build';
  load(url);
});

function build(obj){
  var html = "";
  if (!obj || !obj.feed || !obj.feed.entry) {
    html = '<p class="bold">Not Found</p>';
  }else {
    for (var v in obj.feed.entry) {
      var video = obj.feed.entry[v];
      var thumbnail = video.media$group.media$thumbnail[1]
      html +=
        ' <a href="' + video.link[0].href + '" target="_blank">' +
        '  <img src="' + thumbnail.url + '" title="' + video.title.$t + '"/> '
        ' </a>';
    }
  }
  $('#video').append(html);
}
