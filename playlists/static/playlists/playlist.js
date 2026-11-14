(function () {
  const editToggle = document.getElementById('edit-toggle');
  const editPanel = document.getElementById('edit-panel');
  const reorderHelp = document.querySelector('.reorder-help');
  const playerFrame = document.getElementById('youtube-player');
  const rows = Array.from(document.querySelectorAll('.song-row[data-song-id]'));
  const shuffleToggle = document.getElementById('shuffle-toggle');
  const repeatToggle = document.getElementById('repeat-toggle');
  let ytPlayer = null;
  let queueFirstVideoId = rows[0] ? rows[0].dataset.videoId : null;
  let activeVideoId = new URLSearchParams(window.location.search).get('song') || queueFirstVideoId;
  let shuffleEnabled = false;
  let repeatEnabled = false;
  let playbackOrder = [];

  function setEditMode(editing) {
    if (editPanel) editPanel.hidden = !editing;
    if (reorderHelp) reorderHelp.hidden = !editing;
    document.querySelectorAll('.drag-handle, .remove-song-form').forEach((element) => {
      element.hidden = !editing;
    });
    rows.forEach((row) => { row.draggable = editing; });
    if (editToggle) editToggle.textContent = editing ? 'Done editing' : 'Edit playlist';
    document.body.classList.toggle('editing-playlist', editing);
  }

  if (editToggle) {
    editToggle.addEventListener('click', () => setEditMode(editPanel.hidden));
  }
  if (editPanel && !editPanel.hidden) setEditMode(true);

  function loadYouTubeAPI() {
    if (window.YT && window.YT.Player) {
      createPlayer();
      return;
    }
    const existingScript = document.querySelector('script[src="https://www.youtube.com/iframe_api"]');
    if (!existingScript) {
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(script);
    }
    const previousReady = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = function () {
      if (previousReady) previousReady();
      createPlayer();
    };
  }

  function createPlayer() {
    if (!playerFrame || !window.YT || !window.YT.Player || playerFrame.dataset.ready) return;
    playerFrame.dataset.ready = 'true';
    ytPlayer = new YT.Player(playerFrame, { events: { onStateChange: handlePlayerState } });
  }

  function getRows() {
    return Array.from(document.querySelectorAll('.song-row[data-video-id]'));
  }

  function buildPlaybackOrder() {
    const allRows = getRows();
    if (!shuffleEnabled) return allRows;
    const currentRow = allRows.find((row) => row.dataset.videoId === activeVideoId);
    const remaining = allRows.filter((row) => row !== currentRow);
    for (let index = remaining.length - 1; index > 0; index -= 1) {
      const randomIndex = Math.floor(Math.random() * (index + 1));
      [remaining[index], remaining[randomIndex]] = [remaining[randomIndex], remaining[index]];
    }
    return currentRow ? [currentRow, ...remaining] : remaining;
  }

  function updatePlaybackOrder() {
    playbackOrder = buildPlaybackOrder();
  }

  if (shuffleToggle) {
    shuffleToggle.addEventListener('click', () => {
      shuffleEnabled = !shuffleEnabled;
      shuffleToggle.setAttribute('aria-pressed', String(shuffleEnabled));
      updatePlaybackOrder();
    });
  }
  if (repeatToggle) {
    repeatToggle.addEventListener('click', () => {
      repeatEnabled = !repeatEnabled;
      repeatToggle.setAttribute('aria-pressed', String(repeatEnabled));
    });
  }

  function handlePlayerState(event) {
    if (event.data !== YT.PlayerState.ENDED) return;
    const currentId = event.target.getVideoData().video_id;
    activeVideoId = currentId;
    if (!playbackOrder.length || !playbackOrder.some((row) => row.dataset.videoId === currentId)) updatePlaybackOrder();
    const currentIndex = playbackOrder.findIndex((row) => row.dataset.videoId === currentId);
    const nextRow = playbackOrder[currentIndex + 1] || (repeatEnabled ? playbackOrder[0] : null);
    if (!nextRow) return;
    event.target.loadVideoById(nextRow.dataset.videoId);
    updateNowPlaying(nextRow);
    window.history.replaceState({}, '', `${window.location.pathname}?song=${nextRow.dataset.videoId}`);
  }

  function updateNowPlaying(row) {
    const title = document.getElementById('now-playing-title');
    const channel = document.getElementById('now-playing-channel');
    if (title) title.textContent = row.dataset.title;
    if (channel) channel.textContent = row.dataset.channel;
  }

  if (playerFrame) loadYouTubeAPI();
  if (!rows.length) return;

  let draggedRow = null;
  rows.forEach((row) => {
    row.addEventListener('dragstart', () => {
      draggedRow = row;
      row.classList.add('dragging');
    });
    row.addEventListener('dragend', () => {
      row.classList.remove('dragging');
      draggedRow = null;
      saveOrder();
    });
    row.addEventListener('dragover', (event) => {
      event.preventDefault();
      if (draggedRow && draggedRow !== row) {
        const box = row.getBoundingClientRect();
        row.parentNode.insertBefore(draggedRow, event.clientY < box.top + box.height / 2 ? row : row.nextSibling);
      }
    });
  });

  function saveOrder() {
    const songIds = Array.from(document.querySelectorAll('.song-row[data-song-id]')).map((row) => row.dataset.songId);
    const orderedRows = Array.from(document.querySelectorAll('.song-row[data-song-id]'));
    const firstRow = orderedRows[0];
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(window.location.pathname + 'reorder/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ song_ids: songIds }),
    }).then((response) => {
      if (!response.ok || !firstRow || firstRow.dataset.videoId === queueFirstVideoId) return;
      queueFirstVideoId = firstRow.dataset.videoId;
      activeVideoId = firstRow.dataset.videoId;
      updatePlaybackOrder();
      updateNowPlaying(firstRow);
      if (ytPlayer) ytPlayer.cueVideoById(firstRow.dataset.videoId);
      window.history.replaceState({}, '', `${window.location.pathname}?song=${firstRow.dataset.videoId}`);
    });
  }
}());
