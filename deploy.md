# 🚀 Deployment Guide - Live Website in 2 Minutes

Follow these quick steps to deploy your website online for free. Once complete, you will receive a public link (e.g., `https://regal-auditorium.onrender.com`) that can be opened on any mobile, tablet, or desktop device.

---

## Step 1: Push Code to GitHub

1. Open your browser and go to [GitHub](https://github.com) (sign up for a free account if you don't have one).
2. Click **New Repository** and name it `regal_auditorium`. Leave other settings at default and click **Create repository**.
3. Open a terminal/command prompt in your project folder (`c:\Users\SOORAJ\regal_auditorium`) and run these commands to upload your code:

```bash
git add .
git commit -m "Setup live production website with Docker & Postgres support"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/regal_auditorium.git
git push -u origin main
```
*(Replace `<YOUR_GITHUB_USERNAME>` with your actual GitHub username).*

---

## Step 2: Create a Free Database on Neon

Since cloud services reset temporary local files, we use a cloud database that keeps your inquiries secure forever.

1. Go to [Neon Console](https://neon.tech) and create a free account.
2. Create a new project. Neon will instantly generate a PostgreSQL database.
3. Copy your **Connection String** from the dashboard. It will look like this:
   `postgresql://neondb_owner:xxxxxx@ep-cool-wave-xxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require`

---

## Step 3: Launch live on Render (Free)

1. Go to [Render](https://render.com) and sign up for a free account.
2. Click **New +** (top right) and choose **Web Service**.
3. Link your GitHub account and select your `regal_auditorium` repository.
4. Fill in the following details:
   - **Name**: `regal-auditorium`
   - **Region**: Select the one closest to you (e.g., Singapore or Oregon)
   - **Language**: Select **Docker** (Render will read our `Dockerfile` automatically!)
   - **Instance Type**: Select **Free**
5. Click **Advanced** at the bottom, then click **Add Environment Variable**:
   - **Key**: `DATABASE_URL`
   - **Value**: *(Paste your Neon Connection String from Step 2)*
6. Click **Create Web Service**.

---

### 🎉 That's it!
Render will now build your container, automatically run the database seeder to populate mock bookings, and deploy the live site. Once finished, Render will display your public URL at the top of the dashboard page!
