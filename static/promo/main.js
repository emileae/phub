'use strict';


//var BootState = require('/static/states/boot');
//var MenuState = require('/static/states/menu');
//var PlayState = require('/static/states/play');
//var PreloadState = require('/static/states/preload');

var game = new Phaser.Game(288, 505, Phaser.AUTO, 'flappy-bird-reborn');

// Game States
game.state.add('boot', Game.Boot);
game.state.add('menu', Game.Menu);
game.state.add('play', Game.Play);
game.state.add('preload', Game.Preload);


game.state.start('boot');

  