## [psedge.github.io/hiking](https://psedge.github.io/hiking)

I'm trying to walk a lot more, aiming to improve my stamina and explore my new home; so this is a visualisation
of my progress each year.

### 2020: 1279km
### 2021: ...
 
*Setup*

* Make a Strava dev application at [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
* Import the Terraform module:

```hcl-terraform
module "hiking" {
  source = "./terraform"
  CLIENT_ID = var.CLIENT_ID
  CLIENT_SECRET = var.CLIENT_SECRET
}
```