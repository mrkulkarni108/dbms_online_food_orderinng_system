use food_delivery;

insert into restaurants (name, category, city, image_url)
select 'Burger Hub', 'Fast Food', 'Pune', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=600'
from dual
where not exists (
    select 1 from restaurants where lower(name) = 'burger hub' and lower(city) = 'pune'
);

insert into restaurants (name, category, city, image_url)
select 'Pizza Palace', 'Italian', 'Pune', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=600'
from dual
where not exists (
    select 1 from restaurants where lower(name) = 'pizza palace' and lower(city) = 'pune'
);

insert into restaurants (name, category, city, image_url)
select 'South Spice', 'South Indian', 'Pune', 'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?q=80&w=600'
from dual
where not exists (
    select 1 from restaurants where lower(name) = 'south spice' and lower(city) = 'pune'
);

insert into restaurants (name, category, city, image_url)
select 'North Delight', 'North Indian', 'Pune', 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?q=80&w=600'
from dual
where not exists (
    select 1 from restaurants where lower(name) = 'north delight' and lower(city) = 'pune'
);

insert into restaurants (name, category, city, image_url)
select 'Hyderabadi Biryani House', 'Hyderabadi', 'Pune', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?q=80&w=600'
from dual
where not exists (
    select 1 from restaurants where lower(name) = 'hyderabadi biryani house' and lower(city) = 'pune'
);

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Cheese Burger', 120, 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Cheeseburger.jpg'
from restaurants r
where lower(r.name) = 'burger hub'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'cheese burger'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Veg Burger', 90, 'https://images.unsplash.com/photo-1606755962773-d324e0a13086'
from restaurants r
where lower(r.name) = 'burger hub'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'veg burger'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Margherita Pizza', 200, 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3'
from restaurants r
where lower(r.name) = 'pizza palace'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'margherita pizza'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Farmhouse Pizza', 250, 'https://images.unsplash.com/photo-1594007654729-407eedc4be65'
from restaurants r
where lower(r.name) = 'pizza palace'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'farmhouse pizza'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Masala Dosa', 80, 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976'
from restaurants r
where lower(r.name) = 'south spice'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'masala dosa'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Idli Sambar', 60, 'https://images.unsplash.com/photo-1630383249896-424e482df921'
from restaurants r
where lower(r.name) = 'south spice'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'idli sambar'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Butter Chicken', 220, 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398'
from restaurants r
where lower(r.name) = 'north delight'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'butter chicken'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Paneer Butter Masala', 180, 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d'
from restaurants r
where lower(r.name) = 'north delight'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'paneer butter masala'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Chicken Biryani', 250, 'https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a'
from restaurants r
where lower(r.name) = 'hyderabadi biryani house'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'chicken biryani'
  );

insert into food_items (restaurant_id, name, price, image)
select r.id, 'Veg Biryani', 180, 'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=800&q=80'
from restaurants r
where lower(r.name) = 'hyderabadi biryani house'
  and not exists (
      select 1 from food_items f where f.restaurant_id = r.id and lower(f.name) = 'veg biryani'
  );

insert into users (name, email, password, address, city)
select 'Akash Patil', 'akash@example.com', '$2b$12$b8cEwSuJAd8yjexKx8zNquGb/G6gN1f4y5xULX2LUN04uH0uy6pBC', 'Baner Pune', 'Pune'
from dual
where not exists (
    select 1 from users where lower(email) = 'akash@example.com'
);

insert into users (name, email, password, address, city)
select 'Chinmay Kulkarni', 'chinmay@example.com', '$2b$12$nWuAsqt7KHsgVObMkJP3SeT6BxqStPzXisxN2hnjZEXD69FgE2tFq', 'Wakad Pune', 'Pune'
from dual
where not exists (
    select 1 from users where lower(email) = 'chinmay@example.com'
);

insert into users (name, email, password, address, city)
select 'Ayush Tripathi', 'ayush@example.com', '$2b$12$wDRXm022ckokDTMChm6wJu48vR/QPRyUzI5EiFlxdw7hmvW./8AGa', 'Kothrud Pune', 'Pune'
from dual
where not exists (
    select 1 from users where lower(email) = 'ayush@example.com'
);

insert into addresses (user_id, label, address_line, city, is_default)
select u.id, 'home', u.address, u.city, 1
from users u
where lower(u.email) = 'akash@example.com'
  and not exists (
      select 1 from addresses a where a.user_id = u.id
  );

insert into addresses (user_id, label, address_line, city, is_default)
select u.id, 'home', u.address, u.city, 1
from users u
where lower(u.email) = 'chinmay@example.com'
  and not exists (
      select 1 from addresses a where a.user_id = u.id
  );

insert into addresses (user_id, label, address_line, city, is_default)
select u.id, 'home', u.address, u.city, 1
from users u
where lower(u.email) = 'ayush@example.com'
  and not exists (
      select 1 from addresses a where a.user_id = u.id
  );
