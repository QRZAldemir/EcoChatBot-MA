import { Pipe, PipeTransform } from '@angular/core';
import { Canal } from '../models/canal.model';

@Pipe({ name: 'canalById', standalone: true })
export class CanalByIdPipe implements PipeTransform {
  transform(canais: Canal[], id: number | null | undefined): string {
    if (!id) return '';
    const canal = canais.find(c => c.id === id);
    return canal?.arquivoMenu ?? '';
  }
}
