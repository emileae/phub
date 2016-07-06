
var Game = {};
'use strict';

Game.Boot = function(game) {
}

Game.Boot.prototype = {
  preload: function() {
    this.load.image('preloader', '/static/assets/preloader.gif');
  },
  create: function() {
    this.game.input.maxPointers = 1;
    this.game.state.start('preload');
  }
};

//module.exports = Boot;
