'use strict';

Game.Ground = function(game, x, y, width, height) {
  Phaser.TileSprite.call(this, game, x, y, width, height, 'ground');
  // start scrolling our ground
  this.autoScroll(-150,0);
  
  // enable physics on the ground sprite
  // this is needed for collision detection
  this.game.physics.arcade.enableBody(this);
      
  // we don't want the ground's body
  // to be affected by gravity or external forces
  this.body.allowGravity = false;
  this.body.immovable = true;


};

Game.Ground.prototype = Object.create(Phaser.TileSprite.prototype);
Game.Ground.prototype.constructor = Ground;

Game.Ground.prototype.update = function() {
  
  // write your prefab's specific update code here
  
};

//module.exports = Ground;