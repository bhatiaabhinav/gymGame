import gymGame
import pygame
import numpy as np
from typing import List, Dict

class SimpleSprite(gymGame.GameComponent):
    def __init__(self, sprite, w=1, h=1, static=False):
        super().__init__()
        self.setSize([w, h])
        self.sprite = sprite # type: pygame.Surface
        self.static = static

    def awake(self):
        Camera.instance.spritesBatch.append(self)

    def setSize(self, size):
        self.size = size
    
    def load(filename):
        return pygame.image.load(filename)#.convert_alpha()

    def update(self):
        Camera.instance.spritesBatch.append(self)

class Camera(gymGame.GameComponent):
    instance = None # type: Camera
    # pygame.init()
    # pygame.display.init()
    # screen = pygame.display.set_mode((1,1))
    def __init__(self, renderingSurface, fov, backgroundColor=(0,0,0)):
        super().__init__()
        self.spritesBatch = [] # type: List[SimpleSprite]
        self._dirtyRects = []
        self.setFov(fov)
        self.setRenderingSurface(renderingSurface)
        self.backgroundColor = backgroundColor
        self.staticBackground = None
        self._scaledSprites = {} # type: Dict[SimpleSprite, pygame.Surface]
        Camera.instance = self
        self.latestFrame = np.zeros([210,150,3], dtype=np.uint8)

    def createRenderingSurface(resolution):
        return pygame.Surface(resolution)#.convert_alpha()

    def setRenderingSurface(self, surface):
        self.surface = surface
        self.resolution = (surface.get_width(), surface.get_height())

    def setFov(self, fov):
        self.fov = fov
        self._map_bounds = [[-fov[0]/2, -fov[1]/2], [fov[0]/2, fov[1]/2]]

    def awake(self):
        Camera.instance = self

    def _getCoordinatesOnSurface(self, position):
        x = (position[0] - self._map_bounds[0][0]) * self.resolution[0] // (self._map_bounds[1][0] - self._map_bounds[0][0])
        y = (position[1] - self._map_bounds[0][1]) * self.resolution[1] // (self._map_bounds[1][1] - self._map_bounds[0][1])
        return [x, self.resolution[1] - y]

    def _getSizeOnSurface(self, size):
        return (int((size[0] * self.resolution[0]) / self.fov[0]), int((size[1] * self.resolution[1]) / self.fov[1]))

    def _getScaledSprite(self, ss: SimpleSprite):
        if ss in self._scaledSprites:
            return self._scaledSprites[ss]
        else:
            size = self._getSizeOnSurface(ss.size)
            scaled = pygame.transform.smoothscale(ss.sprite, size)
            self._scaledSprites[ss] = scaled
            return scaled

    def update(self):
        self.render()

    def _drawSpriteComponent(self, sc):
        upperLeft = (sc.gameObject.position[0] - sc.size[0]/2, sc.gameObject.position[1] + sc.size[1]/2)
        dest = self._getCoordinatesOnSurface(upperLeft)
        scaledSprite = self._getScaledSprite(sc)
        rect = (dest, (scaledSprite.get_width(), scaledSprite.get_height()))
        self.surface.blit(scaledSprite, dest)
        return rect

    def _clear(self):
        if self.staticBackground is None:
            self.surface.fill(self.backgroundColor)
            staticSprites = filter(lambda sc:sc.static, self.spritesBatch)
            for sc in staticSprites:
                self._drawSpriteComponent(sc)
            self.staticBackground = self.surface.copy()
        else:
            for r in self._dirtyRects:
                #self.surface.fill(self.backgroundColor, r)
                self.surface.blit(self.staticBackground, r, r)
        self._dirtyRects.clear()

    def render(self):
        self._clear()
        for sc in filter(lambda s: not s.static, self.spritesBatch):
            rect = self._drawSpriteComponent(sc)
            self._dirtyRects.append(rect)
        self.spritesBatch.clear()

    def getLatestFrame(self):
        self.render()
        #if self.latestFrame is not None:
        self.latestFrame = pygame.surfarray.pixels3d(self.surface).copy()
        #self.latestFrame = np.zeros([210,150,3], dtype=np.uint8)
        # pygame.pixelcopy.surface_to_array(self.latestFrame, self.surface)
        self.latestFrame = np.swapaxes(self.latestFrame, 0, 1)
        return self.latestFrame