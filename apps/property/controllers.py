from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from .utils import save_property_images
from ..models.property import Property
from ..models.property_image import PropertyImage
from ..models.favorite import Favorite
from .. import db
from .forms import PropertyForm
from flask_babel import _
from . import property
from .utils import allowed_file, delete_property_image

@property.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    form = PropertyForm()
    if form.validate_on_submit():
        try:
            images = request.files.getlist('images')
            if len(images) < 3:
                flash(_('Veuillez ajouter au moins (3) images'), 'danger')
                return render_template('properties/add_property.html', form=form)
                
            for image in images:
                if not allowed_file(image.filename):
                    flash(_('Type de fichier non supporté'), 'danger')
                    return render_template('properties/add_property.html', form=form)
                if image.content_length > current_app.config['MAX_IMAGE_SIZE']:
                    flash(_('Une des images dépasse 5MB'), 'danger')
                    return render_template('properties/add_property.html', form=form)

            property = Property(
                title=form.title.data,
                description=form.description.data,
                neighborhood=form.neighborhood.data,
                property_type=form.property_type.data,
                rooms=form.rooms.data,
                bathrooms=form.bathrooms.data,
                country=form.country.data,
                shower_type=form.shower_type.data,
                transaction_type=form.transaction_type.data,
                surface=form.surface.data,
                has_courtyard=form.has_courtyard.data,
                has_water=form.has_water.data,
                has_electricity=form.has_electricity.data,
                exact_address=form.exact_address.data,
                whatsapp_contact=form.whatsapp_contact.data,
                phone_contact=form.phone_contact.data,
                price=form.price.data,
                currency=form.currency.data,
                owner_id=current_user.id
            )

            db.session.add(property)
            db.session.commit()

            image_urls = save_property_images(images, folder_name=f"property_images/{current_user.id}")

            for url in image_urls:
                property_image = PropertyImage(
                    filename=url,
                    property_id=property.id
                )
                db.session.add(property_image)

            db.session.commit()

            flash(_('Votre propriété a été ajoutée!'), 'success')
            return redirect(url_for('property.detail', property_id=property.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding property: {str(e)}", exc_info=True)
            flash(_('Une erreur est survenue lors de l\'ajout de la propriété'), 'danger')

    return render_template(
        'properties/add_property.html', 
        form=form,
        title=_('Ajouter une propriété')
    )



@property.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    if property.owner_id != current_user.id:
        abort(403)
    
    form = PropertyForm(obj=property)
    
    if form.validate_on_submit():
        try:
            property.title = form.title.data
            property.description = form.description.data
            property.neighborhood = form.neighborhood.data
            property.property_type = form.property_type.data
            property.rooms = form.rooms.data
            property.bathrooms = form.bathrooms.data
            property.country = form.country.data
            property.shower_type = form.shower_type.data
            property.transaction_type = form.transaction_type.data
            property.surface = form.surface.data
            property.has_courtyard = form.has_courtyard.data
            property.has_water = form.has_water.data
            property.has_electricity = form.has_electricity.data
            property.exact_address = form.exact_address.data
            property.whatsapp_contact = form.whatsapp_contact.data
            property.phone_contact = form.phone_contact.data
            property.price = form.price.data
            property.currency = form.currency.data
            property.is_available = form.is_available.data if hasattr(form, 'is_available') else True
            
            images = request.files.getlist('images')
            if images and images[0].filename != '':
                for image in property.images:
                    delete_property_image(image.filename)
                    db.session.delete(image)
                
                # Save new images
                image_urls = save_property_images(images, folder_name=f"property_images/{current_user.id}")
                for url in image_urls:
                    property_image = PropertyImage(
                        filename=url,
                        property_id=property.id
                    )
                    db.session.add(property_image)
            
            db.session.commit()
            flash(_('Les modifications ont été enregistrées!'), 'success')
            return redirect(url_for('property.detail', property_id=property.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing property: {str(e)}", exc_info=True)
            flash(_('Une erreur est survenue lors de la modification'), 'danger')
    
    return render_template(
        'properties/edit_property.html', 
        form=form,
        property=property,
        title=_('Modifier la propriété')
    )


@property.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    image = PropertyImage.query.get_or_404(image_id)
    property = image.property
    
    if property.owner_id != current_user.id:
        abort(403)
    
    try:
        delete_property_image(image.filename)
        db.session.delete(image)
        db.session.commit()
        flash(_('Image supprimée avec succès'), 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        flash(_('Une erreur est survenue lors de la suppression'), 'danger')
    
    return redirect(url_for('property.edit_property', property_id=property.id))

@property.route('view_property/<int:property_id>', methods=['GET'])
def detail(property_id):
    property = Property.query.get_or_404(property_id)
    return render_template(
        'properties/detail.html', 
        title=property.title,
        property=property
    )



@property.route('/delete_property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if the current user is the owner of the property
    if property.owner_id != current_user.id:
        abort(403)
    
    try:
        # Delete all associated images first
        for image in property.images:
            delete_property_image(image.filename)
        
        db.session.delete(property)
        db.session.commit()
        
        flash(_('La propriété a été supprimée avec succès'), 'success')
        return redirect(url_for('main.home'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting property: {str(e)}", exc_info=True)
        flash(_('Une erreur est survenue lors de la suppression'), 'danger')
        return redirect(url_for('property.detail', property_id=property.id))
    


@property.route('/toggle_favorite/<int:property_id>', methods=['POST'])
@login_required
def toggle_favorite(property_id):
    property = Property.query.get_or_404(property_id)
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        property_id=property.id
    ).first()

    try:
        if favorite:
            # Remove from favorites
            db.session.delete(favorite)
            is_favorite = False
        else:
            # Add to favorites
            favorite = Favorite(user_id=current_user.id, property_id=property.id)
            db.session.add(favorite)
            is_favorite = True
        
        db.session.commit()
        return jsonify({
            'success': True,
            'is_favorite': is_favorite,
            'favorites_count': len(property.favorites)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling favorite: {str(e)}", exc_info=True)
        return jsonify({'success': False}), 500