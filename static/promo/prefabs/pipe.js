'use strict';

Game.Pipe = function(game, x, y, frame) {
  Phaser.Sprite.call(this, game, x, y, 'pipe', frame);
  this.anchor.setTo(0.5, 0.5);
  this.game.physics.arcade.enableBody(this);

  this.body.allowGravity = false;
  this.body.immovable = true;
  
};

Game.Pipe.prototype = Object.create(Phaser.Sprite.prototype);
Game.Pipe.prototype.constructor = Pipe;

Game.Pipe.prototype.update = function() {
  // write your prefab's specific update code here
  
};

//module.exports = Pipe;