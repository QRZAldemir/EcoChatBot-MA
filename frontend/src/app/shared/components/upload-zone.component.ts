import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-upload-zone',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './upload-zone.component.html',
    styleUrls: ['./upload-zone.component.css']
})
export class UploadZoneComponent {
    @Input() title = 'Arquivo';
    @Input() icon = 'fa-file-excel';
    @Input() fileType = 'arquivo';
    @Input() accept = '.xlsx,.xls';
    @Output() fileUploaded = new EventEmitter<{ file: File; tipo: string }>();

    isDragOver = signal(false);
    isLoaded = signal(false);
    fileName = signal('');

    onDragOver(event: DragEvent): void {
        event.preventDefault();
        this.isDragOver.set(true);
    }

    onDragLeave(event: DragEvent): void {
        event.preventDefault();
        this.isDragOver.set(false);
    }

    onDrop(event: DragEvent): void {
        event.preventDefault();
        this.isDragOver.set(false);
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            this.processFile(files[0]);
        }
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.processFile(input.files[0]);
        }
    }

    private processFile(file: File): void {
        this.fileName.set(file.name);
        this.isLoaded.set(true);
        this.fileUploaded.emit({ file, tipo: this.fileType });
    }

    reset(): void {
        this.isLoaded.set(false);
        this.fileName.set('');
    }
}