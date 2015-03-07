$(function() {
	generateMyPlaylist();

	$("#search-button").click(function() {
		var search = $("#video-search").val();
		$.getJSON("/videosearch", {query: search}, function(data) {
			var html = '';
			$.each(data, function(v) {
				html += '<div><iframe width="500" height="310" src="https://www.youtube.com/embed/' 
				+ data[v]['id'] + '" frameborder="0" allowfullscreen></iframe></div><p>' 
				+ data[v]['title'] + '</p><p><button type="button" class="btn btn-success add-video" vid="'
				+ data[v]['id'] +'">Add</button></p>';
			});
			$(".video-list").html(html);
			$(".add-video").click(function() {
				var vid = $(this).attr("vid");
				$.post("/addvideo", {vid:vid}, function(data) {
					if(data == 'error') {
						alert('you\'re not logged in!');
					}
					else {
						generateMyPlaylist();
					}
				}); 
			});

		});
	});

	$('#video-search').keypress(function(e){
    	if(e.which == 13){//Enter key pressed
        	$('#search-button').click();//Trigger search button click event
        }
    });

    function generateMyPlaylist() {
    	$.getJSON("/getplaylist", {}, function(data) {
    		var htmlstring = '';
    		$.each(data, function(v) {
    			htmlstring += '<div><iframe width="350" height="200" src="https://www.youtube.com/embed/' 
    			+ data[v]['vid'] + '" frameborder="0" allowfullscreen></iframe></div>';
    		});
    		$("#playlist").html(htmlstring);
    	});
    }
});

