"use strict";

var CSS_UNITS = 96 / 72;
var pdfDownloadLink = document.getElementById("pdf-download");

PDFJS.workerSrc = PDFJS.workerSrc.replace(/\.js\?/, ".worker.js?");

PDFJS.getDocument(pdfDownloadLink.href).then(function(pdf) {
	var pageElements = [];
	var lastUpdate = 0;
	var stillRendering = {};

	function renderPages() {
		var pixelRatio = window.devicePixelRatio || 1;
		var currentUpdate = ++lastUpdate;

		for (var i = 0; i < pageElements.length; i++) {
			(function(i) {
				pdf.getPage(i + 1).then(function(page) {
					var elements = pageElements[i];
					var canvas;

					if (stillRendering[i]) {
						canvas = document.createElement("canvas");

						if (currentUpdate === lastUpdate) {
							elements.canvas.parentNode.replaceChild(canvas, elements.canvas);
							elements.canvas = canvas;
						}
					} else {
						canvas = elements.canvas;
						stillRendering[i] = true;
					}

					var viewport = page.getViewport(pixelRatio * CSS_UNITS);

					canvas.width = viewport.width;
					canvas.height = viewport.height;
					canvas.style.width = (viewport.width / pixelRatio | 0) + "px";
					canvas.style.height = (viewport.height / pixelRatio | 0) + "px";

					var g = canvas.getContext("2d");

					page.getTextContent().then(function(textContent) {
						while (elements.text.firstChild) {
							elements.text.removeChild(elements.text.firstChild);
						}

						elements.text.style.transform = "scale(" + 1 / pixelRatio + ")";
						elements.text.style.webkitTransform = "scale(" + 1 / pixelRatio + ")";
						elements.text.style.msTransform = "scale(" + 1 / pixelRatio + ")";

						var textLayer = new TextLayerBuilder({
							textLayerDiv: elements.text,
							viewport: viewport,
							pageIndex: i + 1
						});

						textLayer.setTextContent(textContent);
						textLayer.render(200);

						page.render({
							canvasContext: g,
							viewport: viewport
						}).then(function() {
							if (currentUpdate === lastUpdate) {
								stillRendering[i] = false;
							}
						});
					});
				});
			})(i);
		}
	}

	for (var i = 0; i < pdf.pdfInfo.numPages; i++) {
		var container = document.createElement("div");
		container.className = "pdf-page";

		var canvas = document.createElement("canvas");
		canvas.className = "pdf-canvas";

		var text = document.createElement("div");
		text.className = "pdf-text-layer";

		pageElements.push({
			canvas: canvas,
			text: text
		});

		container.appendChild(text);
		container.appendChild(canvas);
		pdfDownloadLink.parentNode.insertBefore(container, pdfDownloadLink);
	}

	renderPages();
	pdfDownloadLink.parentNode.removeChild(pdfDownloadLink);

	window.addEventListener("resize", renderPages, false);
});
