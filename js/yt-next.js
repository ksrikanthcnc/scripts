if (location.host === 'www.youtube.com') {
	if (window.document.getElementsByClassName("ytp-autonav-toggle-button")[0].ariaChecked === 'true') {
		player.addEventListener("onStateChange", function (state) {
			if (state === 0) {
				window.document.getElementsByClassName("ytp-next-button")[0].click()
			}
		});
	}
}

