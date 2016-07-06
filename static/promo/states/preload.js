
'use strict';
Game.Preload = function(game) {
  this.asset = null;
  this.ready = false;
}

Game.Preload.prototype = {
  preload: function() {
    this.asset = this.add.sprite(this.width/2,this.height/2, 'preloader');
    this.asset.anchor.setTo(0.5, 0.5);

    this.load.onLoadComplete.addOnce(this.onLoadComplete, this);
    this.load.setPreloadSprite(this.asset);
    this.load.image('background', '/static/assets/background.png');
    this.load.image('ground', '/static/assets/ground.png');
    this.load.image('title', '/static/assets/title.png');
    this.load.spritesheet('bird', '/static/assets/bird-emile-01.png', 55,54,1);
    this.load.spritesheet('pipe', '/static/assets/pipes.png', 54,320,2);
    this.load.image('startButton', '/static/assets/start-button.png');
    
    this.load.image('instructions', '/static/assets/instructions.png');
    this.load.image('getReady', '/static/assets/get-ready.png');
    
    this.load.image('scoreboard', '/static/assets/scoreboard.png');
    this.load.spritesheet('medals', '/static/assets/medals.png',44, 46, 2);
    this.load.image('gameover', '/static/assets/gameover.png');
    this.load.image('particle', '/static/assets/particle.png');

    this.load.audio('flap', '/static/assets/flap2.wav');
    this.load.audio('pipeHit', '/static/assets/pipe-hit2.wav');
    this.load.audio('groundHit', '/static/assets/ground-hit2.wav');
    this.load.audio('score', '/static/assets/score2.wav');
    this.load.audio('ouch', '/static/assets/ouch.wav');

    this.load.bitmapFont('flappyfont', '/static/assets/fonts/flappyfont/flappyfont.png', '/static/assets/fonts/flappyfont/flappyfont.fnt');

  },
  create: function() {
    this.asset.cropEnabled = false;
  },
  update: function() {
    if(!!this.ready) {
      this.game.state.start('menu');
    }
  },
  onLoadComplete: function() {
    this.ready = true;
  }
};

//module.exports = Preload;
