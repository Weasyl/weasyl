"use strict";

(function () {
	var SVG_NS = "http://www.w3.org/2000/svg";
	var CSS_UNITS = 96 / 72;
	var pdfDownloadLink = document.getElementById("pdf-download");

	//PDFJS.workerSrc = PDFJS.workerSrc.replace(/\.js\?/, ".worker.js?");

	var loadingTask = pdfjsLib.getDocument(pdfDownloadLink.href);

	loadingTask.promise.then(function (pdf) {
		var pageElements = [];
		var lastUpdate = 0;
		var stillRendering = {};

		function renderPages() {
			var pixelRatio = window.devicePixelRatio || 1;
			var currentUpdate = ++lastUpdate;

			for (var i = 0; i < pageElements.length; i++) {
				(function (i) {
					pdf.getPage(i + 1).then(function (page) {
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

						var viewport = page.getViewport({scale: pixelRatio * 1.5});

						canvas.width = viewport.width;
						canvas.height = viewport.height;
						canvas.style.width = (viewport.width / pixelRatio | 0) + "px";
						canvas.style.height = (viewport.height / pixelRatio | 0) + "px";

						elements.text.setAttribute("width", viewport.width);
						elements.text.setAttribute("height", viewport.width);

						var g = canvas.getContext("2d");

						page.getTextContent().then(function (textContent) {
							while (elements.text.firstChild) {
								elements.text.removeChild(elements.text.firstChild);
							}

							elements.text.style.transform = "scale(" + 1 / pixelRatio + ")";
							elements.text.style.webkitTransform = "scale(" + 1 / pixelRatio + ")";
							elements.text.style.msTransform = "scale(" + 1 / pixelRatio + ")";

							textContent.items.forEach(function (item) {
								var matrix = pdfjsLib.Util.transform(
									pdfjsLib.Util.transform(viewport.transform, item.transform),
									[1, 0, 0, -1, 0, 0]
								);

								var style = textContent.styles[item.fontName];

								var node = document.createElementNS(SVG_NS, "text");
								node.setAttribute("transform", "matrix(" + matrix.join(" ") + ")");
								node.setAttribute("font-family", style.fontFamily);
								node.textContent = item.str;
								elements.text.appendChild(node);
							});

							page.render({
								canvasContext: g,
								viewport: viewport
							}).promise.then(function () {
								if (currentUpdate === lastUpdate) {
									stillRendering[i] = false;
								}
							});
						});
					});
				})(i);
			}
		}

		for (var i = 0; i < pdf.numPages; i++) {
			var container = document.createElement("div");
			container.className = "pdf-page";

			var canvas = document.createElement("canvas");
			canvas.className = "pdf-canvas";

			var text = document.createElementNS(SVG_NS, "svg");
			text.setAttribute("class", "pdf-text-layer");
			text.setAttribute("font-size", "1");
			text.setAttribute("fill", "transparent");

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
	}, console.error);
})();
