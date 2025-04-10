import pygame
import pymunk
import random
import math
import colorsys

# Initialize Pygame and Pymunk
pygame.init()
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Endless Platform Jumper")
clock = pygame.time.Clock()

# Physics setup
space = pymunk.Space()
space.gravity = (0, 900)

# Colors
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230, 100)  # Semi-transparent light blue

class BackgroundCircle:
    def __init__(self, depth_layer):
        self.radius = random.randint(20, 80)
        self.x = random.randint(-100, WIDTH + 100)
        self.y = random.randint(-100, HEIGHT + 100)
        self.depth_layer = depth_layer  # 0 is furthest (slowest), 2 is closest (fastest)
        self.parallax_speed = 0.2 + (depth_layer * 0.2)  # Speed increases with layer
        self.alpha = 100 - (depth_layer * 20)  # Transparency varies by layer

    def draw(self, camera):
        # Apply parallax effect based on camera position
        parallax_y = camera.offset_y * self.parallax_speed
        screen_y = self.y - parallax_y
        
        # Wrap around when off screen
        while screen_y > HEIGHT + 100:
            self.y -= HEIGHT + 200
            screen_y = self.y - parallax_y
        while screen_y < -100:
            self.y += HEIGHT + 200
            screen_y = self.y - parallax_y

        # Create surface for semi-transparent circle
        circle_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (*LIGHT_BLUE[:3], self.alpha), 
                         (self.radius, self.radius), self.radius)
        screen.blit(circle_surface, (self.x - self.radius, screen_y - self.radius))

def get_fire_color():
    # Generate warm colors for fire
    hue = random.uniform(0.0, 0.1)  # Red to orange range
    saturation = random.uniform(0.8, 1.0)
    value = random.uniform(0.8, 1.0)
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return tuple(int(x * 255) for x in rgb)

class Camera:
    def __init__(self):
        self.offset_y = 0
        self.target_offset_y = 0
        self.lerp_speed = 0.1

    def update(self, target_y):
        # Calculate target offset to keep player in upper third of screen
        self.target_offset_y = target_y - HEIGHT//3
        # Smooth camera movement
        self.offset_y += (self.target_offset_y - self.offset_y) * self.lerp_speed

    def apply(self, pos):
        return pos[0], pos[1] - self.offset_y

class Player:
    def __init__(self, pos):
        self.size = 30
        self.body = pymunk.Body(1, pymunk.moment_for_box(1, (self.size, self.size)))
        self.body.position = pos
        self.shape = pymunk.Poly.create_box(self.body, (self.size, self.size))
        self.shape.elasticity = 0.8  # Increased bounciness
        self.shape.friction = 0.5
        self.shape.collision_type = 1
        space.add(self.body, self.shape)
        self.health = 100  # Replace lives with health
        self.jump_strength = -400
        self.can_jump = False
        self.mid_air_jump_available = True  # New: Track mid-air jump
        self.score = 0
        self.max_depth = 0
        self.damage_cooldown = 0  # Add cooldown to prevent rapid health loss
        self.damage_cooldown_max = 30  # Half a second at 60 FPS

    def jump(self):
        if self.can_jump:
            self.body.velocity = (self.body.velocity.x, self.jump_strength)
            self.can_jump = False
            self.mid_air_jump_available = True  # Reset mid-air jump when touching platform
        elif self.mid_air_jump_available:  # Allow mid-air jump
            self.body.velocity = (self.body.velocity.x, self.jump_strength)
            self.mid_air_jump_available = False

    def draw(self, camera):
        pos = camera.apply((self.body.position.x, self.body.position.y))
        pygame.draw.rect(screen, YELLOW, 
                        (pos[0] - self.size/2, pos[1] - self.size/2, 
                         self.size, self.size))
        
        # Draw health bar
        bar_width = 50
        bar_height = 5
        health_width = (bar_width * self.health) // 100
        bar_pos = (pos[0] - bar_width//2, pos[1] - self.size//2 - 10)
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), 
                        (bar_pos[0], bar_pos[1], bar_width, bar_height))
        # Foreground (green)
        pygame.draw.rect(screen, (0, 255, 0),
                        (bar_pos[0], bar_pos[1], health_width, bar_height))

    def update(self):
        # Update max depth and score
        current_depth = self.body.position.y
        if current_depth > self.max_depth:
            self.score += int(current_depth - self.max_depth)
            self.max_depth = current_depth
        
        # Update damage cooldown
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

    def take_damage(self, amount):
        if self.damage_cooldown <= 0:
            self.health -= amount
            self.damage_cooldown = self.damage_cooldown_max
            return True
        return False

class Platform:
    def __init__(self, pos, width, is_bouncy=False, depth=0):
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = pos
        
        # Vary shape based on depth
        self.depth = depth
        complexity = min(0.8, depth / 10000)  # Increases with depth, caps at 0.8
        
        if random.random() < complexity:
            # Create irregular platform shape
            num_points = random.randint(3, 6)
            base_width = width
            base_height = 20
            points = []
            
            for i in range(num_points):
                angle = (2 * math.pi * i) / num_points
                radius = random.uniform(base_width/3, base_width/2)
                x = math.cos(angle) * radius
                y = math.sin(angle) * (base_height * random.uniform(0.8, 1.2))
                points.append((x, y))
            
            self.shape = pymunk.Poly(self.body, points)
        else:
            # Regular rectangular platform
            self.shape = pymunk.Poly.create_box(self.body, (width, 20))
        
        # Rotate platform based on depth
        max_rotation = min(math.pi/4, depth/5000)  # Maximum 45 degrees, increases with depth
        self.body.angle = random.uniform(-max_rotation, max_rotation)
        
        self.shape.elasticity = 1.5 if is_bouncy else 0.5
        self.shape.friction = 0.5
        self.shape.collision_type = 2
        self.is_bouncy = is_bouncy
        space.add(self.body, self.shape)
        self.width = width

    def draw(self, camera):
        pos = camera.apply((self.body.position.x, self.body.position.y))
        color = ORANGE if self.is_bouncy else BLUE
        
        # Draw the platform shape
        points = []
        for v in self.shape.get_vertices():
            x = v.rotated(self.body.angle).x + pos[0]
            y = v.rotated(self.body.angle).y + pos[1]
            points.append((x, y))
        
        pygame.draw.polygon(screen, color, points)

class Spike:
    def __init__(self, pos, is_right_side=False):
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = pos
        
        # Create triangle vertices for spike
        size = 20
        if is_right_side:
            vs = [(0, -size), (0, size), (-size, 0)]
        else:
            vs = [(0, -size), (0, size), (size, 0)]
        
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.collision_type = 4  # New collision type for spikes
        space.add(self.body, self.shape)
        self.color = GREY
        self.is_right_side = is_right_side

    def draw(self, camera):
        pos = self.body.position
        points = []
        for v in self.shape.get_vertices():
            x = v.rotated(self.body.angle).x + pos.x
            y = v.rotated(self.body.angle).y + pos.y
            points.append(camera.apply((x, y)))
        pygame.draw.polygon(screen, self.color, points)

class PlatformGenerator:
    def __init__(self):
        self.last_platform_y = HEIGHT - 50
        self.platform_gap = 150
        self.min_width = WIDTH//6
        self.max_width = WIDTH//2
        self.spikes = []  # Store spike objects
        self.generate_boundary_spikes()
        
        # Initialize background circles for parallax effect
        self.bg_circles = []
        for layer in range(3):  # 3 depth layers
            for _ in range(10):  # 10 circles per layer
                self.bg_circles.append(BackgroundCircle(layer))

    def generate_boundary_spikes(self):
        spike_spacing = 40
        for y in range(-1000, 10000, spike_spacing):  # Generate a long stretch of spikes
            self.spikes.append(Spike((0, y), False))  # Left wall
            self.spikes.append(Spike((WIDTH, y), True))  # Right wall

    def generate_platform(self):
        x = random.randint(self.min_width, WIDTH - self.min_width)
        
        # Vary platform width based on depth
        depth_factor = self.last_platform_y / 1000  # Increases with depth
        width_variation = math.sin(depth_factor) * (self.max_width - self.min_width) * 0.3
        base_width = (self.min_width + self.max_width) / 2
        width = base_width + width_variation
        
        # Vary platform gap based on depth
        gap_variation = math.cos(depth_factor) * 50
        self.platform_gap = 150 + gap_variation
        
        is_bouncy = random.random() < 0.3
        self.last_platform_y += self.platform_gap
        return Platform((x, self.last_platform_y), width, is_bouncy, self.last_platform_y)

    def update(self, camera_y, platforms):
        # Generate new platforms ahead
        while self.last_platform_y < camera_y + HEIGHT * 2:
            platforms.append(self.generate_platform())
        
        # Remove platforms that are too far up
        return [p for p in platforms if p.body.position.y > camera_y - HEIGHT]

    def draw_background(self, camera):
        # Draw background circles with parallax effect
        for circle in self.bg_circles:
            circle.draw(camera)

    def draw_spikes(self, camera):
        # Draw only visible spikes
        for spike in self.spikes:
            if camera.offset_y - HEIGHT <= spike.body.position.y <= camera.offset_y + HEIGHT * 2:
                spike.draw(camera)

class Particle:
    def __init__(self, pos):
        self.size = random.uniform(10, 20)  # Random size
        mass = self.size / 15.0  # Adjust mass based on size
        self.body = pymunk.Body(mass, pymunk.moment_for_box(mass, (self.size, self.size)))
        self.body.position = pos
        self.body.velocity = (random.uniform(-100, 100), random.uniform(-300, -200))
        self.body.angular_velocity = random.uniform(-5, 5)
        
        # Create triangle vertices with random variations
        angle_offset = random.uniform(0, math.pi * 2)
        vs = []
        for i in range(3):
            angle = angle_offset + i * (2 * math.pi / 3)
            dist = self.size * random.uniform(0.8, 1.2)  # Vary the points a bit
            vs.append((math.cos(angle) * dist, math.sin(angle) * dist))
        
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.elasticity = 0.5
        self.shape.friction = 0.5
        self.shape.collision_type = 3
        space.add(self.body, self.shape)
        
        self.color = get_fire_color()
        
    def draw(self, camera):
        pos = self.body.position
        points = []
        for v in self.shape.get_vertices():
            x = v.rotated(self.body.angle).x + pos.x
            y = v.rotated(self.body.angle).y + pos.y
            points.append(camera.apply((x, y)))
        
        pygame.draw.polygon(screen, self.color, points)

def handle_collision(arbiter, space, data):
    shapes = arbiter.shapes
    if shapes[0].collision_type == 1:  # Player collision
        if shapes[1].collision_type == 3:  # with Particle
            player_shape = shapes[0]
            particle_shape = shapes[1]
            
            for obj in [player]:
                if obj.shape == player_shape:
                    if obj.take_damage(10):
                        try:
                            if particle_shape.body in space.bodies:
                                space.remove(particle_shape, particle_shape.body)
                        except:
                            pass
                        return False
        elif shapes[1].collision_type == 4:  # with Spike
            player_shape = shapes[0]
            for obj in [player]:
                if obj.shape == player_shape:
                    obj.take_damage(25)  # More damage from spikes
                    return True
    elif shapes[0].collision_type == 3:  # Particle with platform
        try:
            if shapes[0].body in space.bodies:
                space.remove(shapes[0], shapes[0].body)
        except:
            pass
    return True

# Update collision handlers
handler = space.add_collision_handler(1, 3)  # Player and Particle
handler.begin = handle_collision
handler = space.add_collision_handler(2, 3)  # Platform and Particle
handler.begin = handle_collision
handler = space.add_collision_handler(1, 4)  # Player and Spike
handler.begin = handle_collision

# Game objects
camera = Camera()
player = Player((WIDTH//2, HEIGHT//4))
platform_generator = PlatformGenerator()
platforms = [Platform((WIDTH//2, HEIGHT - 50), WIDTH//2)]
particles = []
particle_spawn_timer = 0
particle_spawn_interval = 60
difficulty_timer = 0
difficulty_increase_interval = 600

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()

    # Update
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.body.velocity = (-200, player.body.velocity.y)
    elif keys[pygame.K_RIGHT]:
        player.body.velocity = (200, player.body.velocity.y)
    else:
        player.body.velocity = (0, player.body.velocity.y)

    # Update camera and player
    camera.update(player.body.position.y)
    player.update()

    # Update platforms
    platforms = platform_generator.update(camera.offset_y, platforms)

    # Spawn particles relative to camera position
    particle_spawn_timer += 1
    if particle_spawn_timer >= particle_spawn_interval:
        spawn_y = camera.offset_y + HEIGHT + 20
        particles.append(Particle((random.randint(0, WIDTH), spawn_y)))
        particle_spawn_timer = 0

    # Increase difficulty
    difficulty_timer += 1
    if difficulty_timer >= difficulty_increase_interval:
        particle_spawn_interval = max(10, particle_spawn_interval - 5)
        difficulty_timer = 0

    # Check if player is on platform
    player.can_jump = False
    for p in platforms:
        if abs(player.body.position.y - p.body.position.y) < 30 and \
           abs(player.body.velocity.y) < 0.1:
            player.can_jump = True
            break

    # Check for game over (health <= 0 instead of lives)
    if player.health <= 0:
        running = False
    
    if player.body.position.y < camera.offset_y - 100:
        player.health -= 25  # Damage player for going too high
        player.body.position = (WIDTH//2, camera.offset_y + HEIGHT//2)
        player.body.velocity = (0, 0)

    # Physics update
    space.step(1/60.0)

    # Drawing
    screen.fill((0, 0, 0))
    
    # Draw background first
    platform_generator.draw_background(camera)
    
    # Draw game objects
    platform_generator.draw_spikes(camera)  # Draw spikes
    player.draw(camera)
    for platform in platforms:
        platform.draw(camera)
    
    # Update and draw particles
    for particle in particles[:]:
        if particle.body.position.y < camera.offset_y - 50:
            try:
                if particle.body in space.bodies:
                    space.remove(particle.shape, particle.body)
                particles.remove(particle)
            except:
                particles.remove(particle)
        else:
            particle.draw(camera)

    # Draw HUD
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {player.score//100}', True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()