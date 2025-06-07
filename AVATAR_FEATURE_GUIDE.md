# User Avatar Feature Guide

This guide explains how to use the newly implemented user avatar functionality in the delivery platform.

## Overview

Users can now upload profile pictures (avatars) during registration. The avatar field is optional, allowing users to register with or without a profile picture.

## Features

- ✅ Optional avatar upload during registration
- ✅ Support for common image formats (JPG, PNG, GIF)
- ✅ Automatic file naming using user UUID
- ✅ Organized storage in `media/avatars/` directory
- ✅ Frontend validation for file size and type
- ✅ API support for avatar upload and retrieval

## Database Changes

### CustomUser Model
A new `avatar` field has been added to the `CustomUser` model:

```python
avatar = models.ImageField(_('profile avatar'), upload_to=user_avatar_upload_path, blank=True, null=True)
```

### Migration
The migration `users/migrations/0002_customuser_avatar.py` has been created and applied.

## API Usage

### Registration with Avatar

**Endpoint:** `POST /api/users/register/`

**Content-Type:** `multipart/form-data`

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -F "email=user@example.com" \
  -F "full_name=John Doe" \
  -F "password=securepass123" \
  -F "password_confirm=securepass123" \
  -F "role=CUSTOMER" \
  -F "avatar=@/path/to/profile.jpg" \
  -F "customer_profile={}"
```

**Example using JavaScript (FormData):**
```javascript
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('full_name', 'John Doe');
formData.append('password', 'securepass123');
formData.append('password_confirm', 'securepass123');
formData.append('role', 'CUSTOMER');
formData.append('avatar', avatarFile); // File object from input[type="file"]
formData.append('customer_profile', JSON.stringify({}));

fetch('/api/users/register/', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': csrfToken
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Registration without Avatar

The avatar field is optional. Users can register without providing an avatar:

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "role": "CUSTOMER",
    "customer_profile": {}
  }'
```

### User Profile Response

When retrieving user profiles, the avatar field will be included:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar": "/media/avatars/123e4567-e89b-12d3-a456-426614174000.jpg",
  "role": "CUSTOMER",
  "is_active": true,
  "date_joined": "2025-06-07T14:30:00Z",
  "customer_profile": {
    "default_address": "123 Main St"
  }
}
```

If no avatar is uploaded, the `avatar` field will be `null`.

## Frontend Implementation

### Registration Form

A complete registration form with avatar upload is available at `/register/`. The form includes:

- Email, full name, phone fields
- Avatar upload with preview
- Role selection with dynamic profile fields
- Password and confirmation
- Client-side validation for file size and type

### Avatar Preview

The frontend automatically shows a preview of the selected avatar image before upload.

### File Validation

- **File types:** JPG, PNG, GIF
- **Max size:** 5MB
- **Preview:** Circular crop preview

## File Storage

### Upload Path
Avatars are stored in: `media/avatars/{user_uuid}.{extension}`

### Example Paths
- `media/avatars/123e4567-e89b-12d3-a456-426614174000.jpg`
- `media/avatars/987fcdeb-51a2-43d1-9f12-345678901234.png`

### URL Access
Avatars are accessible via: `/media/avatars/{filename}`

## Admin Interface

The Django admin interface has been updated to include the avatar field:

- Avatar field in user creation form
- Avatar field in user edit form
- Avatar display in user list view

## Testing

A comprehensive test script `test_avatar_functionality.py` is available to verify:

- Avatar upload during registration
- Registration without avatar
- File storage and retrieval
- Cleanup functionality

Run tests with:
```bash
python test_avatar_functionality.py
```

## Security Considerations

1. **File Type Validation:** Only image files are accepted
2. **File Size Limits:** 5MB maximum file size
3. **Secure File Names:** Files are renamed using user UUID
4. **Path Traversal Protection:** Upload path is controlled by Django

## Migration Guide

If you're updating an existing installation:

1. Apply the migration:
   ```bash
   python manage.py migrate users
   ```

2. Update your frontend forms to include the avatar field

3. Ensure media files are properly served in production

## Troubleshooting

### Common Issues

1. **"Pillow not installed"**
   - Solution: `pip install Pillow>=10.1.0`

2. **Avatar not displaying**
   - Check media URL configuration in settings
   - Ensure media files are served correctly

3. **File upload fails**
   - Check file size (max 5MB)
   - Verify file type (images only)
   - Check form enctype is `multipart/form-data`

### Debug Tips

1. Check Django logs for upload errors
2. Verify media directory permissions
3. Test with small image files first
4. Use browser developer tools to inspect form data

## Future Enhancements

Potential improvements for the avatar feature:

- [ ] Image resizing/compression on upload
- [ ] Multiple image sizes (thumbnails)
- [ ] Avatar cropping interface
- [ ] Default avatar images
- [ ] Avatar change history
- [ ] Integration with external image services

---

**Note:** This feature is now fully implemented and ready for use in both development and production environments.